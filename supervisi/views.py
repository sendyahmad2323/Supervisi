from django.shortcuts import render, redirect, get_object_or_404
from .models import FormatSupervisi, ItemFormat, Supervisi, JawabanItem, AspekFormat, JawabanAspek
from .forms import JawabanForm
from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
import base64
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import FormatSupervisiForm, ItemFormatForm, SupervisiForm

# ================== LOGIN / LOGOUT ==================
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect berdasarkan role
            if user.is_staff:
                return redirect('admin_dashboard')  # Admin/Kepala Ruangan
            else:
                return redirect('daftar_format_supervisi')  # Perawat
        else:
            messages.error(request, "Username atau password salah")
    return render(request, 'supervisi/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


# ================== HOME ==================
@login_required
def home(request):
    # Redirect otomatis sesuai role
    if request.user.is_staff:
        return redirect('admin_dashboard')
    else:
        return redirect('daftar_format_supervisi')


# ================== ADMIN / KEPALA RUANGAN ==================
def admin_required(user):
    return user.is_staff

@user_passes_test(admin_required)
def admin_dashboard(request):
    total_supervisi = Supervisi.objects.count()
    supervisi_terakhir = Supervisi.objects.order_by('-tanggal')[:5]
    return render(request, 'admin/dashboard.html', {
        'total_supervisi': total_supervisi,
        'supervisi_terakhir': supervisi_terakhir
    })


@user_passes_test(admin_required)
def daftar_supervisi(request):
    supervisi = Supervisi.objects.all().order_by('-tanggal')
    return render(request, 'admin/daftar_supervisi.html', {'supervisi': supervisi})


@login_required
@user_passes_test(admin_required)
def detail_supervisi(request, id):
    supervisi = get_object_or_404(Supervisi, id=id)
    
    # Ambil semua ItemFormat terkait format supervisi
    items = supervisi.format_supervisi.items.prefetch_related('aspek')
    
    # Ambil jawaban untuk supervisi ini
    jawaban_dict = {j.item.id: j.jawaban for j in supervisi.jawaban.all()}

    return render(request, 'admin/detail_supervisi.html', {
        'supervisi': supervisi,
        'items': items,
        'jawaban_dict': jawaban_dict
    })

@login_required
@user_passes_test(admin_required)
def edit_supervisi(request, pk):
    supervisi_obj = get_object_or_404(Supervisi, pk=pk)

    if request.method == "POST":
        # Harus request.FILES untuk menerima file upload
        form = SupervisiForm(request.POST, request.FILES, instance=supervisi_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Data supervisi berhasil diperbarui.")
            return redirect('daftar_supervisi')
        else:
            # Debug: tampilkan error form di console
            print(form.errors)
    else:
        form = SupervisiForm(instance=supervisi_obj)

    return render(request, 'admin/edit_supervisi.html', {
        'form': form,
        'supervisi_obj': supervisi_obj  # untuk preview TTD lama
    })


@login_required
@user_passes_test(admin_required)
def hapus_supervisi(request, pk):
    supervisi_obj = get_object_or_404(Supervisi, pk=pk)
    if request.method == "POST":
        supervisi_obj.delete()
        messages.success(request, "Data supervisi berhasil dihapus.")
        return redirect('daftar_supervisi')
    return render(request, 'admin/hapus_supervisi.html', {'supervisi': supervisi_obj})

@user_passes_test(admin_required)
def kelola_perawat(request):
    perawat = User.objects.filter(is_staff=False)
    return render(request, 'admin/kelola_perawat.html', {'perawat': perawat})

class PerawatForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

# views.py
from django.shortcuts import render, redirect
from .forms import PerawatForm

def tambah_perawat(request):
    if request.method == 'POST':
        form = PerawatForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff = False
            user.save()
            return redirect('kelola_perawat')
    else:
        form = PerawatForm()
    return render(request, 'admin/tambah_perawat.html', {'form': form})

@user_passes_test(admin_required)
def kelola_format(request):
    formats = FormatSupervisi.objects.all()
    return render(request, 'admin/kelola_format.html', {'formats': formats})

@login_required
@user_passes_test(admin_required)
def detail_format(request, pk):
    format_obj = get_object_or_404(FormatSupervisi, pk=pk)
    return render(request, 'admin/detail_format.html', {'format': format_obj})

@login_required
@user_passes_test(admin_required)
def edit_format(request, pk):
    format_obj = get_object_or_404(FormatSupervisi, pk=pk)
    if request.method == "POST":
        form = FormatSupervisiForm(request.POST, instance=format_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Format berhasil diperbarui.")
            return redirect('kelola_format')
    else:
        form = FormatSupervisiForm(instance=format_obj)
    return render(request, 'admin/edit_format.html', {'form': form})

@login_required
@user_passes_test(admin_required)
def hapus_format(request, pk):
    format_obj = get_object_or_404(FormatSupervisi, pk=pk)
    if request.method == "POST":
        format_obj.delete()
        messages.success(request, "Format berhasil dihapus.")
        return redirect('kelola_format')
    return render(request, 'admin/hapus_format.html', {'format': format_obj})

# ================== PERAWAT ==================
@login_required
def daftar_format_supervisi(request):
    formats = FormatSupervisi.objects.all()
    return render(request, "supervisi/format_list.html", {"formats": formats})


@login_required
def isi_supervisi(request, format_id):
    format_supervisi = get_object_or_404(FormatSupervisi, id=format_id)
    items = format_supervisi.items.prefetch_related('aspek')

    if request.method == 'POST':
        supervisi = Supervisi.objects.create(
            format_supervisi=format_supervisi,
            perawat=request.user
        )

        # loop tiap item dan aspek untuk simpan D/TD
        for item in items:
            for aspek in item.aspek.all():
                d = request.POST.get(f"d_{aspek.id}") == "on"
                td = request.POST.get(f"td_{aspek.id}") == "on"

                JawabanAspek.objects.create(
                    supervisi=supervisi,
                    aspek=aspek,
                    d=d,
                    td=td
                )

        return redirect('daftar_format_supervisi')

    return render(request, 'supervisi/isi_supervisi.html', {'format': format_supervisi, 'items': items})



# ================== HITUNG SKOR ==================
def hitung_skor_total(supervisi_id):
    supervisi = Supervisi.objects.get(id=supervisi_id)
    jawaban = supervisi.jawaban.all()
    total_bobot = sum([j.item.bobot for j in jawaban])
    total_score = sum([j.jawaban * j.item.bobot for j in jawaban])
    supervisi.skor_total = (total_score / total_bobot) * 100 if total_bobot > 0 else 0
    supervisi.save()


def tambah_format_supervisi(request):
    if request.method == 'POST':
        form = FormatSupervisiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('kelola_format')
    else:
        form = FormatSupervisiForm()
    return render(request, 'admin/format_form.html', {'form': form})

def tambah_item_format(request, format_id):
    format_supervisi = get_object_or_404(FormatSupervisi, id=format_id)

    if request.method == 'POST':
        prosedur_index = 0
        while f'prosedur_{prosedur_index}' in request.POST:
            prosedur_text = request.POST.get(f'prosedur_{prosedur_index}').strip()
            if prosedur_text:
                # Simpan ItemFormat (prosedur)
                item = ItemFormat.objects.create(
                    format_supervisi=format_supervisi,
                    pertanyaan=prosedur_text
                )

                # Loop semua aspek untuk prosedur ini
                aspek_index = 0
                while f'aspek_{prosedur_index}_{aspek_index}' in request.POST:
                    nama_aspek = request.POST.get(f'aspek_{prosedur_index}_{aspek_index}').strip()
                    if nama_aspek:
                        d_checked = request.POST.get(f'd_{prosedur_index}_{aspek_index}') == 'on'
                        td_checked = request.POST.get(f'td_{prosedur_index}_{aspek_index}') == 'on'

                        AspekFormat.objects.create(
                            item_format=item,
                            nama_aspek=nama_aspek,
                            d=d_checked,
                            td=td_checked
                        )
                    aspek_index += 1
            prosedur_index += 1

        return redirect('kelola_format')

    return render(request, 'admin/item_form.html', {'format': format_supervisi})
