import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q

from .models import Device, DeviceCategory, DevicePhoto, Document, TouchstoneFile
from .forms import DeviceForm, DevicePhotoForm, DocumentForm, TouchstoneUploadForm
from .touchstone_utils import parse_touchstone, generate_s_param_plot_data


def device_list(request):
    devices = Device.objects.select_related('category').prefetch_related('photos')
    category_slug = request.GET.get('category')
    search = request.GET.get('q')

    if category_slug:
        devices = devices.filter(category__slug=category_slug)
    if search:
        devices = devices.filter(
            Q(asset_tag__icontains=search) |
            Q(name__icontains=search) |
            Q(manufacturer__icontains=search) |
            Q(model_number__icontains=search) |
            Q(serial_number__icontains=search) |
            Q(description__icontains=search)
        )

    categories = DeviceCategory.objects.all()
    return render(request, 'devices/device_list.html', {
        'devices': devices,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search or '',
    })


def device_detail(request, pk):
    device = get_object_or_404(
        Device.objects.select_related('category').prefetch_related(
            'photos', 'documents', 'touchstone_files'
        ),
        pk=pk,
    )
    return render(request, 'devices/device_detail.html', {
        'device': device,
        'photo_form': DevicePhotoForm(),
        'document_form': DocumentForm(),
        'touchstone_form': TouchstoneUploadForm(),
    })


def device_create(request):
    if request.method == 'POST':
        form = DeviceForm(request.POST)
        if form.is_valid():
            device = form.save()
            messages.success(request, f'Device "{device.name}" created.')
            return redirect('device_detail', pk=device.pk)
    else:
        form = DeviceForm()
    return render(request, 'devices/device_form.html', {'form': form, 'title': 'Add Device'})


def device_update(request, pk):
    device = get_object_or_404(Device, pk=pk)
    if request.method == 'POST':
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            device = form.save()
            messages.success(request, f'Device "{device.name}" updated.')
            return redirect('device_detail', pk=device.pk)
    else:
        form = DeviceForm(instance=device)
    return render(request, 'devices/device_form.html', {'form': form, 'title': 'Edit Device', 'device': device})


def device_delete(request, pk):
    device = get_object_or_404(Device, pk=pk)
    if request.method == 'POST':
        name = device.name
        device.delete()
        messages.success(request, f'Device "{name}" deleted.')
        return redirect('device_list')
    return render(request, 'devices/device_confirm_delete.html', {'device': device})


def upload_photo(request, pk):
    device = get_object_or_404(Device, pk=pk)
    if request.method == 'POST':
        form = DevicePhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.device = device
            photo.save()
            messages.success(request, 'Photo uploaded.')
    return redirect('device_detail', pk=pk)


def delete_photo(request, pk):
    photo = get_object_or_404(DevicePhoto, pk=pk)
    device_pk = photo.device.pk
    if request.method == 'POST':
        photo.image.delete()
        photo.delete()
        messages.success(request, 'Photo deleted.')
    return redirect('device_detail', pk=device_pk)


def upload_document(request, pk):
    device = get_object_or_404(Device, pk=pk)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.device = device
            doc.save()
            messages.success(request, 'Document uploaded.')
    return redirect('device_detail', pk=pk)


def delete_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    device_pk = doc.device.pk
    if request.method == 'POST':
        doc.file.delete()
        doc.delete()
        messages.success(request, 'Document deleted.')
    return redirect('device_detail', pk=device_pk)


def upload_touchstone(request, pk):
    device = get_object_or_404(Device, pk=pk)
    if request.method == 'POST':
        form = TouchstoneUploadForm(request.POST, request.FILES)
        if form.is_valid():
            ts = form.save(commit=False)
            ts.device = device
            ts.original_filename = request.FILES['file'].name

            try:
                metadata = parse_touchstone(request.FILES['file'], ts.original_filename)
                ts.port_count = metadata.port_count
                ts.frequency_min_hz = int(metadata.frequency_min_hz)
                ts.frequency_max_hz = int(metadata.frequency_max_hz)
                ts.frequency_npoints = metadata.frequency_npoints
                ts.impedance_ohms = metadata.impedance_ohms
            except Exception as e:
                messages.error(request, f'Error parsing Touchstone file: {e}')
                return redirect('device_detail', pk=pk)

            # Collect key-value parameters from the dynamic form rows
            keys = request.POST.getlist('param_keys')
            values = request.POST.getlist('param_values')
            params = {}
            for k, v in zip(keys, values):
                k = k.strip()
                if k:
                    params[k] = v.strip()
            ts.parameters = params

            ts.save()
            messages.success(request, f'Touchstone file "{ts.original_filename}" uploaded.')
    return redirect('device_detail', pk=pk)


def delete_touchstone(request, pk):
    ts = get_object_or_404(TouchstoneFile, pk=pk)
    device_pk = ts.device.pk
    if request.method == 'POST':
        ts.file.delete()
        ts.delete()
        messages.success(request, 'Touchstone file deleted.')
    return redirect('device_detail', pk=device_pk)


def device_label(request, pk):
    device = get_object_or_404(Device.objects.select_related('category'), pk=pk)
    # Build the absolute URL for the QR code
    device_url = request.build_absolute_uri(
        f'/devices/{device.pk}/'
    )
    return render(request, 'devices/device_label.html', {
        'device': device,
        'device_url': device_url,
    })


def touchstone_detail(request, pk):
    ts = get_object_or_404(TouchstoneFile.objects.select_related('device'), pk=pk)

    plot_data = None
    try:
        plot_data = generate_s_param_plot_data(ts.file.path)
    except Exception as e:
        messages.error(request, f'Error generating plot: {e}')

    return render(request, 'devices/touchstone_detail.html', {
        'touchstone': ts,
        'device': ts.device,
        'plot_data_json': json.dumps(plot_data) if plot_data else None,
    })
