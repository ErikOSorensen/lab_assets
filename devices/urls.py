from django.urls import path
from . import views

urlpatterns = [
    path('', views.device_list, name='device_list'),
    path('devices/add/', views.device_create, name='device_create'),
    path('devices/<uuid:pk>/', views.device_detail, name='device_detail'),
    path('devices/<uuid:pk>/edit/', views.device_update, name='device_update'),
    path('devices/<uuid:pk>/delete/', views.device_delete, name='device_delete'),
    path('devices/<uuid:pk>/label/', views.device_label, name='device_label'),
    path('devices/<uuid:pk>/upload-photo/', views.upload_photo, name='upload_photo'),
    path('devices/<uuid:pk>/upload-document/', views.upload_document, name='upload_document'),
    path('devices/<uuid:pk>/upload-touchstone/', views.upload_touchstone, name='upload_touchstone'),
    path('photos/<uuid:pk>/delete/', views.delete_photo, name='delete_photo'),
    path('documents/<uuid:pk>/delete/', views.delete_document, name='delete_document'),
    path('touchstone/<uuid:pk>/', views.touchstone_detail, name='touchstone_detail'),
    path('touchstone/<uuid:pk>/delete/', views.delete_touchstone, name='delete_touchstone'),
]
