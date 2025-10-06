from django import forms
from .models import JawabanItem, FormatSupervisi, ItemFormat, Supervisi
from django.contrib.auth.models import User

class JawabanForm(forms.ModelForm):
    class Meta:
        model = JawabanItem
        fields = ['jawaban']

class FormatSupervisiForm(forms.ModelForm):
    class Meta:
        model = FormatSupervisi
        fields = ['nama']

class PerawatForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        labels = {
            'username': 'Nama Pengguna',
            'email': 'Email',
        }


class FormatSupervisiForm(forms.ModelForm):
    class Meta:
        model = FormatSupervisi
        fields = ['nama', 'deskripsi']
        widgets = {
            'nama': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masukkan nama format supervisi'
            }),
            'deskripsi': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Masukkan deskripsi (opsional)'
            }),
        }
        labels = {
            'nama': 'Nama Format',
            'deskripsi': 'Deskripsi',
        }

class ItemFormatForm(forms.ModelForm):
    class Meta:
        model = ItemFormat
        fields = ['pertanyaan', 'bobot']
        widgets = {
            'pertanyaan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Masukkan pertanyaan'
            }),
            'bobot': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Masukkan bobot (misal 1.0)'
            }),
        }
        labels = {
            'pertanyaan': 'Pertanyaan',
            'bobot': 'Bobot',
        }

class SupervisiForm(forms.ModelForm):
    class Meta:
        model = Supervisi
        fields = ['skor_total', 'ttd_kepala', 'ttd_file']
        widgets = {
            'skor_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'ttd_kepala': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }