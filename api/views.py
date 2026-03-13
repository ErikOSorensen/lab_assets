import os
import tempfile

from django.http import FileResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

import skrf

from devices.models import DeviceCategory, Device, DevicePhoto, Document, TouchstoneFile
from devices.touchstone_utils import parse_touchstone
from .serializers import (
    DeviceCategorySerializer, DeviceListSerializer, DeviceDetailSerializer,
    DevicePhotoSerializer, DocumentSerializer, TouchstoneFileSerializer,
)


class DeviceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DeviceCategory.objects.all()
    serializer_class = DeviceCategorySerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.select_related('category').prefetch_related(
        'photos', 'documents', 'touchstone_files'
    )
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category__slug', 'is_active', 'manufacturer']
    search_fields = ['asset_tag', 'name', 'manufacturer', 'model_number', 'serial_number', 'description']
    ordering_fields = ['name', 'created_at', 'manufacturer']

    def get_serializer_class(self):
        if self.action == 'list':
            return DeviceListSerializer
        return DeviceDetailSerializer

    @action(detail=True, methods=['get', 'post'], url_path='touchstone')
    def touchstone(self, request, pk=None):
        device = self.get_object()
        if request.method == 'GET':
            files = device.touchstone_files.all()
            serializer = TouchstoneFileSerializer(files, many=True, context={'request': request})
            return Response(serializer.data)

        parser_classes = [MultiPartParser, FormParser]
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        description = request.data.get('description', '')
        parameters = request.data.get('parameters', {})
        if isinstance(parameters, str):
            import json
            try:
                parameters = json.loads(parameters)
            except (json.JSONDecodeError, TypeError):
                parameters = {}

        try:
            metadata = parse_touchstone(file_obj, file_obj.name)
        except Exception as e:
            return Response({'error': f'Invalid Touchstone file: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        # Reset file position after parsing
        file_obj.seek(0)
        ts = TouchstoneFile.objects.create(
            device=device,
            file=file_obj,
            original_filename=file_obj.name,
            description=description,
            parameters=parameters,
            port_count=metadata.port_count,
            frequency_min_hz=int(metadata.frequency_min_hz),
            frequency_max_hz=int(metadata.frequency_max_hz),
            frequency_npoints=metadata.frequency_npoints,
            impedance_ohms=metadata.impedance_ohms,
        )
        serializer = TouchstoneFileSerializer(ts, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='photos')
    def photos(self, request, pk=None):
        device = self.get_object()
        if request.method == 'GET':
            photos = device.photos.all()
            serializer = DevicePhotoSerializer(photos, many=True, context={'request': request})
            return Response(serializer.data)

        file_obj = request.FILES.get('image')
        if not file_obj:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        photo = DevicePhoto.objects.create(
            device=device,
            image=file_obj,
            caption=request.data.get('caption', ''),
            is_primary=request.data.get('is_primary', False),
        )
        serializer = DevicePhotoSerializer(photo, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='documents')
    def documents(self, request, pk=None):
        device = self.get_object()
        if request.method == 'GET':
            docs = device.documents.all()
            serializer = DocumentSerializer(docs, many=True, context={'request': request})
            return Response(serializer.data)

        file_obj = request.FILES.get('file')
        url = request.data.get('url', '')
        if not file_obj and not url:
            return Response({'error': 'Provide either a file or a URL (or both).'}, status=status.HTTP_400_BAD_REQUEST)

        title = request.data.get('title', '')
        if not title:
            title = file_obj.name if file_obj else url

        doc = Document.objects.create(
            device=device,
            file=file_obj or '',
            url=url,
            title=title,
            doc_type=request.data.get('doc_type', 'other'),
        )
        serializer = DocumentSerializer(doc, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TouchstoneFileViewSet(viewsets.GenericViewSet):
    queryset = TouchstoneFile.objects.all()
    serializer_class = TouchstoneFileSerializer

    def destroy(self, request, pk=None):
        ts = self.get_object()
        ts.file.delete()
        ts.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        ts = self.get_object()
        return FileResponse(
            open(ts.file.path, 'rb'),
            as_attachment=True,
            filename=ts.original_filename,
        )

    @action(detail=True, methods=['get'])
    def network(self, request, pk=None):
        ts = self.get_object()
        try:
            net = skrf.Network(ts.file.path)
            import numpy as np
            data = {
                'id': str(ts.id),
                'filename': ts.original_filename,
                'parameters': ts.parameters,
                'port_count': net.number_of_ports,
                'frequency_hz': net.f.tolist(),
                'frequency_unit': 'Hz',
                'z0': net.z0[0].real.tolist(),
                's_real': net.s.real.tolist(),
                's_imag': net.s.imag.tolist(),
            }
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PhotoViewSet(viewsets.GenericViewSet):
    queryset = DevicePhoto.objects.all()
    serializer_class = DevicePhotoSerializer

    def destroy(self, request, pk=None):
        photo = self.get_object()
        photo.image.delete()
        photo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentViewSet(viewsets.GenericViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def destroy(self, request, pk=None):
        doc = self.get_object()
        if doc.file:
            doc.file.delete()
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
