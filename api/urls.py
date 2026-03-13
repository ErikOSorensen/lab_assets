from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.DeviceCategoryViewSet)
router.register(r'devices', views.DeviceViewSet)
router.register(r'touchstone', views.TouchstoneFileViewSet)
router.register(r'photos', views.PhotoViewSet)
router.register(r'documents', views.DocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
