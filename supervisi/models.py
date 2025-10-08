from django.db import models
from django.contrib.auth.models import User

class FormatSupervisi(models.Model):
    nama = models.CharField(max_length=255)
    deskripsi = models.TextField(blank=True, null=True)

    def jumlah_aspek(self):
        return sum(item.aspek.count() for item in self.items.all())

    def __str__(self):
        return self.nama


class ItemFormat(models.Model):
    format_supervisi = models.ForeignKey(FormatSupervisi, on_delete=models.CASCADE, related_name='items')
    pertanyaan = models.TextField()
    bobot = models.FloatField(default=1)

    def __str__(self):
        return self.pertanyaan


class AspekFormat(models.Model):
    item_format = models.ForeignKey(ItemFormat, on_delete=models.CASCADE, related_name='aspek')
    nama_aspek = models.CharField(max_length=500)
    d = models.BooleanField(default=False)
    td = models.BooleanField(default=False)

    def __str__(self):
        return self.nama_aspek


class Supervisi(models.Model):
    format_supervisi = models.ForeignKey(FormatSupervisi, on_delete=models.CASCADE)
    perawat = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supervisi_perawat')
    kepala_ruangan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervisi_kepala')
    perawat_nama = models.CharField("Nama Perawat (custom)", max_length=255, blank=True, null=True)
    kepala_nama = models.CharField("Nama Kepala Ruangan (custom)", max_length=255, blank=True, null=True)
    kepala_nip  = models.CharField("NIP Kepala Ruangan (custom)", max_length=100, blank=True, null=True)
    tanggal = models.DateField(auto_now_add=True)

    TIM_CHOICES = [(i, f"Tim {i}") for i in range(1, 5)]
    tim = models.IntegerField(choices=TIM_CHOICES, default=1)

    JENJANG_CHOICES = [
        ('PK I', 'PK I'),
        ('PK II', 'PK II'),
        ('PK III', 'PK III'),
        ('PK IV', 'PK IV'),
    ]
    jenjang_pk = models.CharField(max_length=20, choices=JENJANG_CHOICES, default='PK I')

    ruang = models.CharField(max_length=100, default='Imdad Hamid Lantai 2')

    skor_total = models.FloatField(default=0)
    ttd_perawat = models.ImageField(upload_to='ttd/', null=True, blank=True)
    ttd_kepala = models.ImageField(upload_to='ttd/', null=True, blank=True)
    ttd_file = models.ImageField(upload_to='ttd/', blank=True, null=True)

    def hitung_skor(self):
        jawaban = self.jawaban_aspek.all()
        total_dikerjakan = sum(1 for j in jawaban if j.d)
        total_dinilai = sum(1 for j in jawaban if (j.d or j.td))
        self.skor_total = (total_dikerjakan / total_dinilai * 100) if total_dinilai > 0 else 0
        self.save()
        return self.skor_total

    def __str__(self):
        return f"Supervisi {self.perawat.username} - {self.format_supervisi.nama}"


class JawabanItem(models.Model):
    supervisi = models.ForeignKey(Supervisi, on_delete=models.CASCADE, related_name='jawaban')
    item = models.ForeignKey(ItemFormat, on_delete=models.CASCADE)
    jawaban = models.FloatField()


class JawabanAspek(models.Model):
    supervisi = models.ForeignKey(Supervisi, on_delete=models.CASCADE, related_name='jawaban_aspek')
    aspek = models.ForeignKey(AspekFormat, on_delete=models.CASCADE)
    d = models.BooleanField(default=False)
    td = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.aspek.nama_aspek} - {'D' if self.d else ''}{'TD' if self.td else ''}"
