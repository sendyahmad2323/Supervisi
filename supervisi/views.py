from django.shortcuts import render, redirect, get_object_or_404
from .models import FormatSupervisi, ItemFormat, Supervisi, AspekFormat, JawabanAspek
from .forms import (
    JawabanForm,
    FormatSupervisiForm,
    ItemFormatForm,
    SupervisiForm,
    RegisterForm,
    AkunForm,
    AkunUpdateForm,
)
from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg
from django.forms import inlineformset_factory
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# ================== HELPERS (ROLE) ==================
def admin_required(user):
    """Dipakai user_passes_test untuk halaman admin. Kita pakai is_staff."""
    return user.is_staff


# ================== REGISTER ==================
def register(request):
    """
    Registrasi disederhanakan -> semua user baru adalah Perawat.
    (Tidak ada opsi Kepala Ruangan di UI).
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            perawat_group, _ = Group.objects.get_or_create(name="Perawat")
            user.groups.add(perawat_group)
            user.is_staff = False
            user.save()

            login(request, user)
            messages.success(request, "Registrasi berhasil. Selamat datang!")
            return redirect("daftar_format_supervisi")
    else:
        form = RegisterForm()

    return render(request, "supervisi/register.html", {"form": form})


# ================== LOGIN / LOGOUT ==================
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_dashboard' if user.is_staff else 'daftar_format_supervisi')
        messages.error(request, "Username atau password salah")
    return render(request, 'supervisi/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


# ================== HOME (AUTO-REDIRECT) ==================
@login_required
def home(request):
    return redirect('admin_dashboard' if request.user.is_staff else 'daftar_format_supervisi')


# ================== ADMIN / KEPALA RUANGAN ==================
def detail_supervisi_admin(request, supervisi_id):
    supervisi = get_object_or_404(Supervisi, id=supervisi_id)
    return render(request, 'admin/detail_supervisi.html', {'supervisi': supervisi})


def admin_dashboard(request):
    total_supervisi = Supervisi.objects.count()
    supervisi_terakhir = Supervisi.objects.order_by('-tanggal')[:10]
    return render(request, 'admin/dashboard.html', {
        'total_supervisi': total_supervisi,
        'supervisi_terakhir': supervisi_terakhir,
    })


@user_passes_test(admin_required)
def daftar_supervisi(request):
    supervisi = Supervisi.objects.all().order_by('-tanggal')
    return render(request, 'admin/daftar_supervisi.html', {'supervisi': supervisi})


def detail_supervisi(request, supervisi_id):
    """
    Halaman detail hasil supervisi (Admin):
    - Upload TTD Perawat / Kepala
    - Edit Nama Kepala Ruangan & NIP (baru)
    """
    supervisi = get_object_or_404(Supervisi, id=supervisi_id)

    if request.method == "POST":
        # Simpan info kepala ruangan (nama & NIP)
        if 'save_kepala_info' in request.POST:
            supervisi.kepala_nama = request.POST.get('kepala_nama', '').strip() or None
            supervisi.kepala_nip = request.POST.get('kepala_nip', '').strip() or None
            supervisi.save()
            messages.success(request, "Informasi Kepala Ruangan berhasil disimpan.")
            return redirect('detail_supervisi', supervisi_id=supervisi.id)

        # Upload TTD Perawat
        if 'upload_ttd_perawat' in request.POST:
            supervisi.ttd_perawat = request.FILES.get('ttd_perawat')
            supervisi.save()
            messages.success(request, "TTD Perawat berhasil diupload.")
            return redirect('detail_supervisi', supervisi_id=supervisi.id)

        # Upload TTD Kepala
        if 'upload_ttd_kepala' in request.POST:
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
def kelola_akun(request):
    perawat_group, _ = Group.objects.get_or_create(name="Perawat")
    kepala_group, _ = Group.objects.get_or_create(name="Kepala Ruangan")

    perawat = User.objects.filter(groups=perawat_group).order_by('username')
    kepala_ruangan = User.objects.filter(groups=kepala_group).order_by('username')

    context = {
        'perawat': perawat,
        'kepala_ruangan': kepala_ruangan,
        'current': 'kelola_akun',
    }
    return render(request, 'admin/kelola_perawat.html', context)


@user_passes_test(admin_required)
def tambah_akun(request):
    role = request.POST.get('role') or request.GET.get('role') or 'perawat'
    if role not in ('perawat', 'kepala'):
        role = 'perawat'

    if request.method == 'POST':
        form = AkunForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = (role == 'kepala')
            user.set_password(form.cleaned_data['password'])
            user.save()

            group_name = "Kepala Ruangan" if role == 'kepala' else "Perawat"
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

            role_label = "Kepala Ruangan" if role == 'kepala' else "Perawat"
            messages.success(request, f"Akun {role_label} berhasil ditambahkan.")
            return redirect('kelola_akun')
    else:
        form = AkunForm()
    context = {
        'form': form,
        'current': 'kelola_akun',
        'default_role': role,
    }
    return render(request, 'admin/tambah_perawat.html', context)


@user_passes_test(admin_required)
def edit_akun(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)

    perawat_group, _ = Group.objects.get_or_create(name="Perawat")
    kepala_group, _ = Group.objects.get_or_create(name="Kepala Ruangan")

    current_role = 'kepala' if user_obj.groups.filter(name="Kepala Ruangan").exists() else 'perawat'

    if request.method == 'POST':
        form = AkunUpdateForm(request.POST, instance=user_obj)
        role = request.POST.get('role', current_role)
        if role not in ('perawat', 'kepala'):
            role = 'perawat'

        if form.is_valid():
            akun = form.save(commit=False)
            akun.is_staff = (role == 'kepala')
            new_password = form.cleaned_data.get('password')
            if new_password:
                akun.set_password(new_password)
            akun.save()

            akun.groups.clear()
            if role == 'kepala':
                akun.groups.add(kepala_group)
            else:
                akun.groups.add(perawat_group)

            role_label = "Kepala Ruangan" if role == 'kepala' else "Perawat"
            messages.success(request, f"Akun {role_label} berhasil diperbarui.")
            return redirect('kelola_akun')
    else:
        form = AkunUpdateForm(instance=user_obj)
        role = current_role

    context = {
        'form': form,
        'user_obj': user_obj,
        'current_role': role,
        'current': 'kelola_akun',
    }
    return render(request, 'admin/edit_akun.html', context)


@user_passes_test(admin_required)
def hapus_akun(request, user_id):
    perawat_group, _ = Group.objects.get_or_create(name="Perawat")
    kepala_group, _ = Group.objects.get_or_create(name="Kepala Ruangan")

    user_queryset = User.objects.filter(groups__in=[perawat_group, kepala_group]).distinct()
    user_obj = get_object_or_404(user_queryset, pk=user_id)

    if user_obj == request.user:
        messages.error(request, "Anda tidak dapat menghapus akun Anda sendiri.")
        return redirect('kelola_akun')

    if request.method == 'POST':
        username = user_obj.username
        role_label = "Kepala Ruangan" if user_obj.groups.filter(name="Kepala Ruangan").exists() else "Perawat"
        user_obj.delete()
        messages.success(request, f"Akun {role_label} '{username}' berhasil dihapus.")
        return redirect('kelola_akun')

    context = {
        'user_obj': user_obj,
        'current': 'kelola_akun',
    }
    return render(request, 'admin/hapus_akun.html', context)


@user_passes_test(admin_required)
def kelola_format(request):
    formats = FormatSupervisi.objects.all().prefetch_related('items__aspek')
    context = {
        'formats': formats,
        'current': 'kelola_format',
    }
    return render(request, 'admin/kelola_format.html', context)


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
    """
    Isi supervisi (Perawat). TTD Perawat opsional.
    """
    format_supervisi = get_object_or_404(FormatSupervisi, id=format_id)
    items = format_supervisi.items.prefetch_related('aspek')

    if request.method == 'POST':
        tim = request.POST.get('tim')
        jenjang_pk = request.POST.get('jenjang_pk')
        ruang = request.POST.get('ruang', 'Imdad Hamid Lantai 2')
        perawat_nama = request.POST.get('perawat_nama', '').strip()
        if not perawat_nama:
            perawat_nama = request.user.get_full_name().strip() if request.user.get_full_name() else request.user.username

        supervisi = Supervisi.objects.create(
            format_supervisi=format_supervisi,
            perawat=request.user,
            perawat_nama=perawat_nama,
            tim=tim,
            jenjang_pk=jenjang_pk,
            ruang=ruang,
            ttd_perawat=request.FILES.get('ttd_perawat')  # opsional
        )

        total_d = 0
        total_item = 0

        for item in items:
            for aspek in item.aspek.all():
                d = request.POST.get(f"d_{aspek.id}") == "on"
                td = request.POST.get(f"td_{aspek.id}") == "on"

                if d or td:
                    total_item += 1
                    if d:
                        total_d += 1

                JawabanAspek.objects.create(
                    supervisi=supervisi,
                    aspek=aspek,
                    d=d,
                    td=td
                )

        supervisi.skor_total = (total_d / total_item) * 100 if total_item > 0 else 0
        supervisi.save()

        messages.success(request, "Data supervisi berhasil disimpan.")
        return redirect('daftar_format_supervisi')

    default_perawat_nama = request.user.get_full_name().strip() if request.user.get_full_name() else request.user.username

    return render(request, 'supervisi/isi_supervisi.html', {
        'format': format_supervisi,
        'items': items,
        'default_perawat_nama': default_perawat_nama,
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
        "status_done": done(s),
        "status_label": "Selesai" if done(s) else "Menunggu TTD",
    } for s in qs]

    total = qs.count()
    selesai = sum(1 for s in qs if done(s))
    avg_skor = qs.aggregate(r=Avg('skor_total'))['r'] or 0

    return render(request, "supervisi/ringkasan_saya.html", {
        "cards": cards,
        "summary": {
            "total": total,
            "avg": round(avg_skor, 1),
            "selesai": selesai,
            "menunggu": total - selesai,
        }
    })


# ================== HITUNG SKOR ==================
def hitung_skor_total(supervisi_id):
    s = Supervisi.objects.get(id=supervisi_id)
    jawaban = s.jawaban.all()
    total_bobot = sum([j.item.bobot for j in jawaban])
    total_score = sum([j.jawaban * j.item.bobot for j in jawaban])
    s.skor_total = (total_score / total_bobot) * 100 if total_bobot > 0 else 0
    s.save()


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
                item = ItemFormat.objects.create(
                    format_supervisi=format_supervisi,
                    pertanyaan=prosedur_text
                )
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

    return render(request, 'admin/item_form.html', {
        'format': format_supervisi,
        'current': 'kelola_format',
    })


@login_required
@user_passes_test(admin_required)
def edit_item_format(request, item_id):
    item = get_object_or_404(ItemFormat.objects.select_related('format_supervisi'), pk=item_id)

    if request.method == 'POST' and 'delete_item' in request.POST:
        format_name = item.format_supervisi.nama
        item.delete()
        messages.success(request, f"Item pada format '{format_name}' berhasil dihapus.")
        return redirect('kelola_format')

    if request.method == 'POST' and 'delete_aspek_id' in request.POST:
        aspek_id = request.POST.get('delete_aspek_id')
        aspek = get_object_or_404(AspekFormat, pk=aspek_id, item_format=item)
        aspek.delete()
        messages.success(request, "Aspek penilaian berhasil dihapus.")
        return redirect('edit_item_format', item_id=item.id)

    AspekFormSet = inlineformset_factory(
        ItemFormat,
        AspekFormat,
        fields=['nama_aspek', 'd', 'td'],
        extra=1,
        can_delete=True,
        widgets={
            'nama_aspek': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masukkan aspek'
            }),
            'd': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'td': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )

    if request.method == 'POST':
        form = ItemFormatForm(request.POST, instance=item)
        formset = AspekFormSet(request.POST, instance=item, prefix='aspek')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Item format berhasil diperbarui.")
            return redirect('kelola_format')
    else:
        form = ItemFormatForm(instance=item)
        formset = AspekFormSet(instance=item, prefix='aspek')

    context = {
        'form': form,
        'formset': formset,
        'item': item,
        'format_obj': item.format_supervisi,
        'current': 'kelola_format',
    }
    return render(request, 'admin/edit_item.html', context)


@login_required
@user_passes_test(admin_required)
def hapus_item_format(request, item_id):
    item = get_object_or_404(ItemFormat.objects.select_related('format_supervisi'), pk=item_id)
    format_name = item.format_supervisi.nama

    if request.method == 'POST':
        item.delete()
        messages.success(request, f"Item pada format '{format_name}' berhasil dihapus.")
        return redirect('kelola_format')

    context = {
        'item': item,
        'format_obj': item.format_supervisi,
        'current': 'kelola_format',
    }
    return render(request, 'admin/hapus_item.html', context)


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
        topMargin=1.6*cm, bottomMargin=1.4*cm
    )

    css = getSampleStyleSheet()
    st_title = ParagraphStyle('title', parent=css['Normal'],
                              fontName='Times-Bold', fontSize=14, leading=18,
                              alignment=1, spaceAfter=14, spaceBefore=2)
    st_small = ParagraphStyle('small', parent=css['Normal'],
                              fontName='Times-Roman', fontSize=11.5, leading=13)

    elements = []

    # Judul
    elements.append(Paragraph("FORM SUPERVISI KEPERAWATAN MONITORING BALANCE CAIRAN", st_title))
    elements.append(Spacer(1, 6))

    iw = doc.width

    # Info
    perawat_display = (
        s.perawat_nama
        or (s.perawat.get_full_name() if s.perawat and s.perawat.get_full_name() else None)
        or (s.perawat.username if s.perawat else "")
    )

    col_info_label = 0.22 * iw
    col_info_value = 0.28 * iw
    info_rows = [
        [
            Paragraph("<b>Perawat</b>", st_small),
            Paragraph(perawat_display, st_small),
            Paragraph("<b>Skor Total</b>", st_small),
            Paragraph(f"{s.skor_total:.1f}%", st_small),
        ],
        [
            Paragraph("<b>Ruang</b>", st_small),
            Paragraph(s.ruang, st_small),
            Paragraph("<b>Tim</b>", st_small),
            Paragraph(f"Tim {s.tim}", st_small),
        ],
        [
            Paragraph("<b>Jenjang PK</b>", st_small),
            Paragraph(s.jenjang_pk, st_small),
            "", ""
        ],
    ]
    info_tbl = Table(
        info_rows,
        colWidths=[col_info_label, col_info_value, col_info_label, col_info_value]
    )
    info_tbl.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Times-Roman', 12),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(info_tbl)
    elements.append(Spacer(1, 8))

    # Tabel utama
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

    # Spasi sebelum tanda tangan
    elements.append(Spacer(1, 36))

    # Label tanda tangan
    col_signature = iw / 2
    lbl = Table([["PERAWAT YANG DI SUPERVISI", "SUPERVISOR"]],
                colWidths=[col_signature, col_signature])
    lbl.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), 'Times-Bold', 12),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 28),
    ]))
    elements.append(lbl)

    # Gambar TTD
    left_img = Image(s.ttd_perawat.path, width=4*cm, height=2.3*cm) if s.ttd_perawat else Spacer(1, 2.3*cm)
    right_img = Image(s.ttd_kepala.path, width=4*cm, height=2.3*cm) if s.ttd_kepala else Spacer(1, 2.3*cm)
    ttd = Table([[left_img, right_img]], colWidths=[col_signature, col_signature])
    ttd.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(ttd)

    # Nama + NIP kepala (ambil dari input admin/detail_supervisi.html jika diisi)
    sup_name = (s.kepala_nama or
                (s.kepala_ruangan.get_full_name() if s.kepala_ruangan and s.kepala_ruangan.get_full_name()
                 else (s.kepala_ruangan.username if s.kepala_ruangan else "")))
    sup_nip = s.kepala_nip or ""

    nurse_name = perawat_display or ""

    name_cells = [
        [
            Paragraph(
                f"<para align='center'><u>{nurse_name}</u></para>",
                st_small
            ),
            Paragraph(
                f"<para align='center'><u>{sup_name}</u>{('<br/>NIP : ' + sup_nip) if sup_nip else ''}</para>",
                st_small
            )
        ]
    ]
    names = Table(name_cells, colWidths=[col_signature, col_signature])
    names.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(names)

    doc.build(elements)
    return response
