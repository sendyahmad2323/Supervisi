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
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.http import HttpResponse
import os


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

def detail_supervisi_admin(request, supervisi_id):
    # Ambil data supervisi berdasarkan ID
    supervisi = get_object_or_404(Supervisi, id=supervisi_id)

    context = {
        'supervisi': supervisi,
    }
    return render(request, 'admin/detail_supervisi.html', context)

def admin_dashboard(request):
    total_supervisi = Supervisi.objects.count()
    supervisi_terakhir = Supervisi.objects.order_by('-tanggal')[:10]

    context = {
        'total_supervisi': total_supervisi,
        'supervisi_terakhir': supervisi_terakhir,
    }
    return render(request, 'admin/dashboard.html', context)

@user_passes_test(admin_required)
def daftar_supervisi(request):
    supervisi = Supervisi.objects.all().order_by('-tanggal')
    return render(request, 'admin/daftar_supervisi.html', {'supervisi': supervisi})


def detail_supervisi(request, supervisi_id):
    supervisi = get_object_or_404(Supervisi, id=supervisi_id)

    # proses upload TTD
    if request.method == "POST":
        if 'upload_ttd_perawat' in request.POST:
            supervisi.ttd_perawat = request.FILES.get('ttd_perawat')
            supervisi.save()
            messages.success(request, "TTD Perawat berhasil diupload.")
            return redirect('detail_supervisi', supervisi_id=supervisi.id)

        elif 'upload_ttd_kepala' in request.POST:
            supervisi.ttd_kepala = request.FILES.get('ttd_kepala')
            supervisi.save()
            messages.success(request, "TTD Kepala Ruangan berhasil diupload.")
            return redirect('detail_supervisi', supervisi_id=supervisi.id)

    return render(request, 'admin/detail_supervisi.html', {'supervisi': supervisi})

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
        tim = request.POST.get('tim')
        jenjang_pk = request.POST.get('jenjang_pk')
        ruang = request.POST.get('ruang', 'Imdad Hamid Lantai 2')

        supervisi = Supervisi.objects.create(
            format_supervisi=format_supervisi,
            perawat=request.user,
            tim=tim,
            jenjang_pk=jenjang_pk,
            ruang=ruang
        )

        total_d = 0
        total_item = 0

        # Loop tiap item dan aspek untuk simpan D/TD/TDD
        for item in items:
            for aspek in item.aspek.all():
                d = request.POST.get(f"d_{aspek.id}") == "on"
                td = request.POST.get(f"td_{aspek.id}") == "on"
                tdd = request.POST.get(f"tdd_{aspek.id}") == "on"

                if not tdd:  # hanya dihitung kalau bukan TDD
                    total_item += 1
                    if d:
                        total_d += 1

                JawabanAspek.objects.create(
                    supervisi=supervisi,
                    aspek=aspek,
                    d=d,
                    td=td
                )

        # Hitung skor akhir
        if total_item > 0:
            supervisi.skor_total = (total_d / total_item) * 100
        else:
            supervisi.skor_total = 0
        supervisi.save()

        messages.success(request, "Data supervisi berhasil disimpan.")
        return redirect('daftar_format_supervisi')

    return render(request, 'supervisi/isi_supervisi.html', {
        'format': format_supervisi,
        'items': items
    })



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

def cetak_supervisi_pdf(request, supervisi_id):
    from .models import Supervisi  # sesuaikan path model
    supervisi = Supervisi.objects.get(id=supervisi_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="supervisi_{supervisi.id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('title', fontSize=14, leading=16, alignment=1, spaceAfter=10, spaceBefore=5)
    style_table = ParagraphStyle('table', fontSize=10, leading=12)
    style_normal = ParagraphStyle('normal', fontSize=11, leading=13)

    elements = []

    # Judul
    elements.append(Paragraph("<b>FORM SUPERVISI KEPERAWATAN MONITORING BALANCE CAIRAN</b>", style_title))
    elements.append(Spacer(1, 10))

    # Header informasi supervisi
    info_data = [
        ["Perawat:", supervisi.perawat.username],
        ["Tim:", f"Tim {supervisi.tim}"],
        ["Ruang:", supervisi.ruang],
        ["Jenjang PK:", supervisi.jenjang_pk],
        ["Skor Total:", f"{supervisi.skor_total:.1f}%"]
    ]
    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))

    # Data tabel supervisi
    data = [['PROSEDUR', 'ASPEK YANG DINILAI', 'D', 'TD']]

    for item in supervisi.format_supervisi.items.all():
        aspek_list = list(item.aspek.all())
        for i, aspek in enumerate(aspek_list):
            if i == 0:
                data.append([
                    Paragraph(item.pertanyaan, style_table),
                    Paragraph(aspek.nama_aspek, style_table),
                    "✓" if supervisi.jawaban_aspek.filter(aspek=aspek, d=True).exists() else "",
                    "✓" if supervisi.jawaban_aspek.filter(aspek=aspek, td=True).exists() else "",
                ])
            else:
                data.append([
                    "",
                    Paragraph(aspek.nama_aspek, style_table),
                    "✓" if supervisi.jawaban_aspek.filter(aspek=aspek, d=True).exists() else "",
                    "✓" if supervisi.jawaban_aspek.filter(aspek=aspek, td=True).exists() else "",
                ])

    table = Table(data, colWidths=[4*cm, 9*cm, 1.2*cm, 1.2*cm])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('ALIGN', (-2, 1), (-1, -1), 'CENTER'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 30))

    # Bagian tanda tangan
    elements.append(Paragraph("<b>Perawat yang Disupervisi</b>", style_normal))
    elements.append(Paragraph("<b>Supervisor</b>", style_normal))
    elements.append(Spacer(1, 40))

    # Gambar tanda tangan
    tanda_tangan_row = []
    ttd_dir = os.path.join('media')

    if supervisi.ttd_perawat:
        ttd_perawat_path = supervisi.ttd_perawat.path
        tanda_tangan_row.append(Image(ttd_perawat_path, width=4*cm, height=2*cm))
    else:
        tanda_tangan_row.append(Paragraph("(Belum ada tanda tangan)", style_table))

    if supervisi.ttd_kepala:
        ttd_kepala_path = supervisi.ttd_kepala.path
        tanda_tangan_row.append(Image(ttd_kepala_path, width=4*cm, height=2*cm))
    else:
        tanda_tangan_row.append(Paragraph("(Belum ada tanda tangan)", style_table))

    ttd_table = Table([tanda_tangan_row], colWidths=[7*cm, 7*cm])
    ttd_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(ttd_table)

    # Nama bawah tanda tangan
    nama_ttd = [[
        Paragraph(f"({supervisi.perawat.username})", style_table),
        Paragraph(f"({supervisi.kepala_ruangan or 'Supervisor'})", style_table)
    ]]
    nama_table = Table(nama_ttd, colWidths=[7*cm, 7*cm])
    nama_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(nama_table)

    doc.build(elements)
    return response
