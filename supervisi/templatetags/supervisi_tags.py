from django import template

register = template.Library()

@register.filter
def sum_aspek(items):
    """
    Mengembalikan jumlah total aspek dari semua item.
    Misal: jumlah semua aspek dari semua item dalam format supervisi.
    """
    return sum(item.aspek.count() for item in items)
# supervis
@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})

@register.filter
def count_ttd(supervisi_list, status=True):
    """
    Menghitung jumlah supervisi dengan ttd_kepala = True atau False
    """
    return sum(1 for s in supervisi_list if s.ttd_kepala == status)

@register.filter
def avg_skor(supervisi_list):
    """Menghitung rata-rata skor supervisi"""
    if not supervisi_list:
        return 0
    return round(sum(s.skor_total for s in supervisi_list) / len(supervisi_list), 2)