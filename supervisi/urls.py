from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path("register/", views.register, name="register"), 
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('admin/supervisi/<int:supervisi_id>/pdf/', views.cetak_supervisi_pdf, name='cetak_supervisi_pdf'),

    # Perawat
    path('ringkasan/', views.ringkasan_saya, name='ringkasan_saya'),
    path('formats/', views.daftar_format_supervisi, name='daftar_format_supervisi'),
    path('tambah/', views.tambah_format_supervisi, name='tambah_format_supervisi'),
    path('tambah-item/<int:format_id>/', views.tambah_item_format, name='tambah_item_format'),
    path('formats/<int:format_id>/isi/', views.isi_supervisi, name='isi_supervisi'),
    
    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/supervisi/', views.daftar_supervisi, name='daftar_supervisi'),
    path('admin/supervisi/<int:supervisi_id>/', views.detail_supervisi, name='detail_supervisi'),
    path('supervisi/<int:pk>/hapus/', views.hapus_supervisi, name='hapus_supervisi'),
    path('admin/akun/', views.kelola_akun, name='kelola_akun'),
    path('admin/akun/tambah/', views.tambah_akun, name='tambah_akun'),
    path('admin/akun/<int:user_id>/edit/', views.edit_akun, name='edit_akun'),
    path('admin/format/', views.kelola_format, name='kelola_format'),
    path('format/<int:pk>/', views.detail_format, name='detail_format'),
    path('format/<int:pk>/edit/', views.edit_format, name='edit_format'),
    path('format/<int:pk>/hapus/', views.hapus_format, name='hapus_format'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
