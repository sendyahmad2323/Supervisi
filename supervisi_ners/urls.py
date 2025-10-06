from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='daftar_format_supervisi', permanent=False)),
    path('', include('supervisi.urls')),
]

# Tambahkan jika menggunakan media
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
