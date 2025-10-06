from django.shortcuts import render, redirect, get_object_or_404
from .models import FormatSupervisi, ItemFormat, Supervisi, JawabanItem, AspekFormat, JawabanAspek
from .forms import JawabanForm
from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.core.files.base import ContentFile
import base64
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import FormatSupervisiForm, ItemFormatForm, SupervisiForm, RegisterForm
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.http import HttpResponse
from django.db.models import Avg, Q, Count
from django.template.loader import render_to_string
import os

# ================== HELPERS (ROLE) ==================
def hanya_kepala(view_func):
    """Decorator: izinkan hanya user yang termasuk Kepala Ruangan (berbasis group)."""
    from django.http import HttpResponseForbidden
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.groups.filter(name="Kepala Ruangan").exists():
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Akses khusus Kepala Ruangan.")
    return _wrapped

def admin_required(user):
    """Dipakai user_passes_test untuk halaman admin.
       Kita konsisten gunakan is_staff (di-set saat register untuk Kepala Ruangan)."""
    return user.is_staff

# ================== REGISTER ==================
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Pastikan group ada
            kepala_group, _ = Group.objects.get_or_create(name="Kepala Ruangan")
            perawat_group, _ = Group.objects.get_or_create(name="Perawat")

            # Assign group + set is_staff berdasar pilihan role
            selected_role = getattr(user, "_selected_role", "perawat")
            if selected_role == "kepala":
                user.groups.add(kepala_group)
                user.is_staff = True      # <- penting agar diarahkan ke dashboard admin
            else:
                user.groups.add(perawat_group)
                user.is_staff = False

            user.save()

            # Auto login & redirect sesuai peran
            login(request, user)
            messages.success(request, "Registrasi berhasil. Selamat datang!")

            if user.is_staff:
                return redirect("admin_dashboard")          # Kepala Ruangan
            return redirect("daftar_format_supervisi")      # Perawat
    else:
        form = RegisterForm()

    # Flags helper untuk template (opsional)
    return render(request, "supervisi/register.html", {
        "form": form,
        "is_kepala": request.user.is_authenticated and request.user.groups.filter(name="Kepala Ruangan").exists(),
        "is_perawat": request.user.is_authenticated and request.user.groups.filter(name="Perawat").exists(),
    })

# ================== LOGIN / LOGOUT ==================
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect berdasarkan peran (is_staff = Kepala Ruangan)
            return redirect('admin_dashboard' if user.is_staff else 'daftar_format_supervisi')
        else:
            messages.error(request, "Username atau password salah")
    return render(request, 'supervisi/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')

# ================== HOME (AUTO-REDIRECT) ==================
@login_required
def home(request):
    # Redirect otomatis sesuai role
    return redirect('admin_dashboard' if request.user.is_staff else 'daftar_format_supervisi')

# ================== ADMIN / KEPALA RUANGAN ==================
def detail_supervisi_admin(request, supervisi_id):
    supervisi = get_object_or_404(Supervisi, id=supervisi_id)
    context = { 'supervisi': supervisi }
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
            ruang=ruang,
            ttd_perawat=request.FILES.get('ttd_perawat')  
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
        supervisi.skor_total = (total_d / total_item) * 100 if total_item > 0 else 0
        supervisi.save()

        messages.success(request, "Data supervisi berhasil disimpan.")
        return redirect('daftar_format_supervisi')

    return render(request, 'supervisi/isi_supervisi.html', {
        'format': format_supervisi,
        'items': items
    })

@login_required
def ringkasan_saya(request):
    qs = Supervisi.objects.filter(perawat=request.user).select_related('format_supervisi')

    def done(s):
      return bool(s.ttd_perawat and s.ttd_kepala)

    cards = [{
        "id": s.id,
        "judul": s.format_supervisi.nama,
        "skor": round(s.skor_total or 0, 1),
        "progress": max(0, min(100, s.skor_total or 0)),
        "status_done": done(s),                            # True = selesai, False = menunggu TTD
        "status_label": "Selesai" if done(s) else "Menunggu TTD",
    } for s in qs]

    total = qs.count()
    selesai = sum(1 for s in qs if done(s))
    avg_skor = qs.aggregate(r=Avg('skor_total'))['r'] or 0

    context = {
        "cards": cards,
        "summary": {
            "total": total,
            "avg": round(avg_skor, 1),
            "selesai": selesai,
            "menunggu": total - selesai,
        }
    }
    return render(request, "supervisi/ringkasan_saya.html", context)

# ================== HITUNG SKOR ==================
def hitung_skor_total(supervisi_id):
    supervisi = Supervisi.objects.get(id=supervisi_id)
    jawaban = supervisi.jawaban.all()
    total_bobot = sum([j.item.bobot for j in jawaban])
    total_score = sum([j.jawaban * j.item.bobot for j in jawaban])
    supervisi.skor_total = (total_score / total_bobot) * 100 if total_bobot > 0 else 0
    supervisi.save()

# ================== FORMAT (ADMIN) ==================
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

# ================== CETAK PDF (ReportLab, layout seperti HTML) ==================
def cetak_supervisi_pdf(request, supervisi_id):
    s = get_object_or_404(Supervisi.objects.select_related(
        "format_supervisi", "perawat", "kepala_ruangan"
    ), id=supervisi_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="supervisi_{s.id}.pdf"'

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        leftMargin=1.4*cm, rightMargin=1.4*cm,
        topMargin=1.4*cm, bottomMargin=1.4*cm
    )

    css = getSampleStyleSheet()
    st_title = ParagraphStyle('title', parent=css['Normal'],
                              fontName='Times-Bold', fontSize=14, leading=16,
                              alignment=1, spaceAfter=14, spaceBefore=5)
    st_base = ParagraphStyle('base', parent=css['Normal'],
                              fontName='Times-Roman', fontSize=12, leading=14)
    st_small = ParagraphStyle('small', parent=css['Normal'],
                              fontName='Times-Roman', fontSize=11.5, leading=13)

    elements = []

    # ======= Judul =======
    elements.append(Paragraph("FORM SUPERVISI KEPERAWATAN MONITORING BALANCE CAIRAN", st_title))
    elements.append(Spacer(1, 10))

    # ======= Info Table =======
    iw = doc.width
    info_data = [
        ["Perawat", f": {s.perawat.username}", "Tim", f": Tim {s.tim}"],
        ["Ruang", f": {s.ruang}", "Jenjang PK", f": {s.jenjang_pk}"],
        ["Skor Total", f": {s.skor_total:.1f}%", "", ""],
    ]
    info_tbl = Table(info_data, colWidths=[0.20*iw, 0.30*iw, 0.20*iw, 0.30*iw])
    info_tbl.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Times-Roman', 12),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(info_tbl)
    elements.append(Spacer(1, 12))

    # ======= Main Table =======
    col1 = 0.25 * iw
    colD = 0.075 * iw
    colTD = 0.075 * iw
    col2 = iw - (col1 + colD + colTD)

    data = [
        [Paragraph("<b>PROSEDUR</b>", st_small),
         Paragraph("<b>ASPEK YANG DINILAI</b>", st_small),
         Paragraph("<b>PENILAIAN</b>", st_small), ""],
        ["", "", Paragraph("<b>D</b>", st_small), Paragraph("<b>TD</b>", st_small)]
    ]

    for item in s.format_supervisi.items.all():
        aspek_list = list(item.aspek.all())
        for idx, aspek in enumerate(aspek_list):
            jd = "✓" if s.jawaban_aspek.filter(aspek=aspek, d=True).exists() else ""
            jtd = "✓" if s.jawaban_aspek.filter(aspek=aspek, td=True).exists() else ""
            data.append([
                Paragraph(item.pertanyaan if idx == 0 else "", st_small),
                Paragraph(f"{idx+1}. {aspek.nama_aspek}", st_small),
                Paragraph(f"<para align='center'>{jd}</para>", st_small),
                Paragraph(f"<para align='center'>{jtd}</para>", st_small),
            ])

    tbl = Table(data, colWidths=[col1, col2, colD, colTD])
    tbl.setStyle(TableStyle([
        ('SPAN', (0,0), (0,1)),
        ('SPAN', (1,0), (1,1)),
        ('SPAN', (2,0), (3,0)),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BOX',  (0,0), (-1,-1), 1, colors.black),
        ('FONT', (0,0), (-1,1), 'Times-Bold', 12),
        ('ALIGN', (0,0), (-1,1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (2,2), (3,-1), 'CENTER'),
        ('FONT', (0,2), (-1,-1), 'Times-Roman', 12),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,0), (-1,1), colors.whitesmoke),
    ]))
    elements.append(tbl)

    # ======= Tambah jarak besar sebelum tanda tangan =======
    elements.append(Spacer(1, 40))

    # ======= Footer =======
    lbl = Table([["PERAWAT YANG DI SUPERVISI", "SUPERVISOR"]],
                colWidths=[iw/2, iw/2])
    lbl.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Times-Bold', 12),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 30),
    ]))
    elements.append(lbl)

    # Tanda tangan (gambar)
    left_img = Image(s.ttd_perawat.path, width=4*cm, height=2.3*cm) if s.ttd_perawat else Spacer(1, 2.3*cm)
    right_img = Image(s.ttd_kepala.path, width=4*cm, height=2.3*cm) if s.ttd_kepala else Spacer(1, 2.3*cm)
    ttd = Table([[left_img, right_img]], colWidths=[iw/2, iw/2])
    ttd.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(ttd)

    # Nama + NIP
    sup_name = (s.kepala_ruangan.get_full_name()
                if s.kepala_ruangan and s.kepala_ruangan.get_full_name()
                else "Ns. Riska Sabrianli, S.Kep., M.Kep")
    names = Table([
        [Paragraph(f"<u>{s.perawat.username}</u>", st_small),
         Paragraph(f"<u>{sup_name}</u><br/>NIP : 198211220060801", st_small)]
    ], colWidths=[iw/2, iw/2])
    names.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(names)

    doc.build(elements)
    return response