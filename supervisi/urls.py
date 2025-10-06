from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'), 
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    # Perawat
    path('tambah_perawat/', views.tambah_perawat, name='tambah_perawat'),
    path('formats/', views.daftar_format_supervisi, name='daftar_format_supervisi'),
    path('tambah/', views.tambah_format_supervisi, name='tambah_format_supervisi'),
    path('tambah-item/<int:format_id>/', views.tambah_item_format, name='tambah_item_format'),
    path('formats/<int:format_id>/isi/', views.isi_supervisi, name='isi_supervisi'),
    
    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/supervisi/', views.daftar_supervisi, name='daftar_supervisi'),
    path('admin/supervisi/<int:id>/', views.detail_supervisi, name='detail_supervisi'),
    path('supervisi/<int:pk>/edit/', views.edit_supervisi, name='edit_supervisi'),
    path('supervisi/<int:pk>/hapus/', views.hapus_supervisi, name='hapus_supervisi'),
    path('admin/perawat/', views.kelola_perawat, name='kelola_perawat'),
    path('admin/format/', views.kelola_format, name='kelola_format'),
    path('format/<int:pk>/', views.detail_format, name='detail_format'),
    path('format/<int:pk>/edit/', views.edit_format, name='edit_format'),
    path('format/<int:pk>/hapus/', views.hapus_format, name='hapus_format'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)