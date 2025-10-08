from django import forms
from .models import JawabanItem, FormatSupervisi, ItemFormat, Supervisi
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ('perawat', 'Perawat'),
    ('kepala', 'Kepala Ruangan'),
]

class RegisterForm(UserCreationForm):
    full_name = forms.CharField(
        label="Nama Lengkap",
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Masukkan nama lengkap'})
    )
    email = forms.EmailField(
        label="Email", required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'Masukkan email (opsional)'})
    )
    role = forms.ChoiceField(
        label="Daftar sebagai",
        choices=ROLE_CHOICES,
        widget=forms.Select()
    )

    class Meta:
        model = User
        fields = ("username", "full_name", "email", "password1", "password2", "role")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Masukkan username"}),
            "password1": forms.PasswordInput(attrs={"placeholder": "Masukkan password"}),
            "password2": forms.PasswordInput(attrs={"placeholder": "Ulangi password"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # pecah full_name -> first_name + last_name sederhana
        full = self.cleaned_data.get("full_name", "").strip()
        parts = full.split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
        user._selected_role = self.cleaned_data.get("role")  # dipakai di view
        return user

class JawabanForm(forms.ModelForm):
    class Meta:
        model = JawabanItem
        fields = ['jawaban']

class FormatSupervisiForm(forms.ModelForm):
    class Meta:
        model = FormatSupervisi
        fields = ['nama']

class AkunForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'Nama Pengguna',
            'email': 'Email',
        }


class AkunUpdateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Password Baru",
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email']
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
