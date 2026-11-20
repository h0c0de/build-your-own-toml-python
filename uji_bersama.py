"""Mesin uji build 24 melawan suite resmi toml-test.

Manifes `files-toml-1.0.0` (di ../toml-ref) adalah
daftar wasitnya: 208 valid dibandingkan SEMANTIK ke
JSON resmi (bukan string mentah — float dibandingkan
nilainya, pecahan detik dinormalkan per grup 3 digit
sesuai encoder referensi), 501 invalid wajib ditolak.
Berkas yang tidak terunduh (8 berkas encoding rusak
yang ditolak konektor GitHub) dilewati TERBUKA dengan
catatan, tidak dihitung lulus.
"""

import json
import math
import os

import tomlku

DIR_UJI = os.path.join(os.path.dirname(__file__), "..",
                       "toml-ref", "tests")
MANIFES = os.path.join(DIR_UJI, "files-toml-1.0.0")


def _frac_kanonik(frac):
    if not frac:
        return ""
    while len(frac) % 3:
        frac += "0"
    return "." + frac


def _cocok(milik, harap, jalur="$"):
    """Bandingkan nilai parser vs node JSON resmi."""
    if isinstance(harap, dict) and \
            set(harap) == {"type", "value"} and \
            isinstance(harap.get("type"), str):
        tipe, nilai = harap["type"], harap["value"]
        if tipe == "string":
            return isinstance(milik, str) and milik == nilai
        if tipe == "bool":
            return isinstance(milik, bool) and \
                milik == (nilai == "true")
        if tipe == "integer":
            return isinstance(milik, int) and \
                not isinstance(milik, bool) and \
                milik == int(nilai)
        if tipe == "float":
            if not isinstance(milik, float):
                return False
            harap_f = float(nilai)
            if math.isnan(harap_f) or math.isnan(milik):
                return math.isnan(harap_f) and math.isnan(milik)
            if milik == 0.0 and harap_f == 0.0:
                return math.copysign(1, milik) == \
                    math.copysign(1, harap_f)
            return milik == harap_f
        if tipe == "datetime":
            if not isinstance(milik, tomlku.TanggalWaktu) \
                    or milik.offset is None:
                return False
            dasar = "%sT%s" % (milik.tanggal,
                               _waktu_str(milik.waktu))
            if milik.offset == 0:
                dasar += "Z"
            else:
                tanda = "+" if milik.offset >= 0 else "-"
                o = abs(milik.offset)
                dasar += "%s%02d:%02d" % (tanda, o // 60,
                                          o % 60)
            return dasar == nilai
        if tipe == "datetime-local":
            if not isinstance(milik, tomlku.TanggalWaktu) \
                    or milik.offset is not None:
                return False
            return "%sT%s" % (milik.tanggal,
                              _waktu_str(milik.waktu)) == nilai
        if tipe == "date-local":
            return isinstance(milik, tomlku.Tanggal) and \
                str(milik) == nilai
        if tipe == "time-local":
            return isinstance(milik, tomlku.Waktu) and \
                _waktu_str(milik) == nilai
        raise AssertionError("tipe tak dikenal: %s" % tipe)
    if isinstance(harap, dict):
        if not isinstance(milik, dict):
            return False
        if set(milik) != set(harap):
            return False
        return all(_cocok(milik[k], harap[k],
                          jalur + "." + k) for k in harap)
    if isinstance(harap, list):
        if not isinstance(milik, list) or \
                len(milik) != len(harap):
            return False
        return all(_cocok(a, b, jalur + "[]")
                   for a, b in zip(milik, harap))
    raise AssertionError("bentuk harap tak dikenal di %s"
                         % jalur)


def _waktu_str(w):
    return "%02d:%02d:%02d%s" % (
        w.jam, w.menit, w.detik, _frac_kanonik(w.pecahan))


def jalankan(awalan=None):
    """Jalankan manifes (opsional: hanya entri yang
    mengandung salah satu awalan). Kembalikan
    (lulus, total_dihitung, daftar_gagal, dilewati)."""
    entri = [l.strip() for l in open(MANIFES)
             if l.strip()]
    lulus = 0
    total = 0
    gagal = []
    dilewati = []
    for rel in entri:
        if rel.endswith(".json"):
            continue  # pendamping valid, bukan uji sendiri
        if awalan and not any(a in rel for a in awalan):
            continue
        path = os.path.join(DIR_UJI, rel)
        if rel.endswith(".multi"):
            dilewati.append(rel + " (format .multi)")
            continue
        if not os.path.exists(path):
            dilewati.append(rel + " (tidak terunduh)")
            continue
        mentah = open(path, "rb").read()
        if rel.startswith("valid/"):
            total += 1
            try:
                hasil = tomlku.muat(mentah)
            except tomlku.GalatToml as e:
                gagal.append((rel, "galat: %s" % e))
                continue
            harap = json.load(open(path[:-5] + ".json"))
            if _cocok(hasil, harap):
                lulus += 1
            else:
                gagal.append((rel, "nilai beda: %r vs %r"
                              % (hasil, harap)))
        else:  # invalid/
            total += 1
            try:
                hasil = tomlku.muat(mentah)
            except tomlku.GalatToml:
                lulus += 1
                continue
            gagal.append((rel, "diterima padahal invalid: "
                          "%r" % (hasil,)))
    return lulus, total, gagal, dilewati


if __name__ == "__main__":
    lulus, total, gagal, dilewati = jalankan()
    print("SKOR: %d/%d (dilewati %d)"
          % (lulus, total, len(dilewati)))
    for rel, pesan in gagal[:40]:
        print(" GAGAL %s — %s" % (rel, pesan[:150]))
