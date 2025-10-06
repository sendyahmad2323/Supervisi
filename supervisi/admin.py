from django.contrib import admin
from .models import FormatSupervisi, ItemFormat, AspekFormat, Supervisi, JawabanItem, JawabanAspek

class AspekFormatInline(admin.TabularInline):
    model = AspekFormat
    extra = 1

class ItemFormatInline(admin.TabularInline):
    model = ItemFormat
    extra = 1

@admin.register(FormatSupervisi)
class FormatSupervisiAdmin(admin.ModelAdmin):
    list_display = ('nama', 'deskripsi')
    inlines = [ItemFormatInline]

@admin.register(ItemFormat)
class ItemFormatAdmin(admin.ModelAdmin):
    list_display = ('pertanyaan', 'format_supervisi', 'bobot')
    inlines = [AspekFormatInline]

@admin.register(Supervisi)
class SupervisiAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tanggal',
        'perawat',
        'format_supervisi',
        'tim',
        'jenjang_pk',
        'ruang',
        'skor_total',
        'kepala_ruangan',
    )
    list_filter = ('format_supervisi', 'tim', 'ruang', 'tanggal')
    search_fields = ('perawat__username', 'format_supervisi__nama', 'jenjang_pk', 'ruang')

@admin.register(JawabanAspek)
class JawabanAspekAdmin(admin.ModelAdmin):
    list_display = ('supervisi', 'aspek', 'd', 'td')

admin.site.register(JawabanItem)
