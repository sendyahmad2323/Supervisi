from django.db import models
from django.contrib.auth.models import User

class FormatSupervisi(models.Model):
    nama = models.CharField(max_length=255)
    deskripsi = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.nama

class ItemFormat(models.Model):
    format_supervisi = models.ForeignKey(FormatSupervisi, on_delete=models.CASCADE, related_name='items')
    pertanyaan = models.TextField()
    bobot = models.FloatField(default=1)
    def __str__(self):
        return self.pertanyaan

class AspekFormat(models.Model):
    item_format = models.ForeignKey(
        ItemFormat, 
        on_delete=models.CASCADE, 
        related_name='aspek'  # <- ini wajib ada
    )
    nama_aspek = models.CharField(max_length=500)
    d = models.BooleanField(default=False)
    td = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nama_aspek} ({'D' if self.d else ''}{'TD' if self.td else ''})"


class Supervisi(models.Model):
    format_supervisi = models.ForeignKey(FormatSupervisi, on_delete=models.CASCADE)
    perawat = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supervisi_perawat')
    kepala_ruangan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervisi_kepala')
    tanggal = models.DateField(auto_now_add=True)
    skor_total = models.FloatField(default=0)
    ttd_perawat = models.ImageField(upload_to='ttd/', null=True, blank=True)
    ttd_kepala = models.ImageField(upload_to='ttd/', null=True, blank=True)
    ttd_file = models.ImageField(upload_to='ttd/', blank=True, null=True)
    
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

