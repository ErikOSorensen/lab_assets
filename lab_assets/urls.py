from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('devices.urls')),
]

# Serve uploaded media files directly.
# Normally you'd use nginx for this, but for a small internal app on
# Tailscale served by Gunicorn this is fine.
urlpatterns += [
    path('media/<path:path>', static_serve, {'document_root': settings.MEDIA_ROOT}),
]
