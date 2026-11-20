"""Irisan 5 — final: seluruh manifes TOML 1.0.0
(709 uji terhitung; 8 dilewati terbuka: 7 berkas
encoding rusak yang ditolak konektor GitHub + 1
format .multi) + diferensial vs tomllib pada semua
kasus valid.
"""
import datetime as dt
import math
import os
import tomllib

import tomlku
from uji_bersama import DIR_UJI, MANIFES, jalankan


def ke_biasa(v):
    """Kelas tanggal/waktu build ini -> objek stdlib
    (pecahan dipotong ke mikrodetik seperti tomllib)."""
    if isinstance(v, tomlku.TanggalWaktu):
        mikro = int((v.waktu.pecahan + "000000")[:6]
                    or 0)
        dasar = dt.datetime(v.tanggal.tahun,
                            v.tanggal.bulan,
                            v.tanggal.hari, v.waktu.jam,
                            v.waktu.menit, v.waktu.detik,
                            mikro)
        if v.offset is None:
            return dasar
        return dasar.replace(tzinfo=dt.timezone(
            dt.timedelta(minutes=v.offset)))
    if isinstance(v, tomlku.Tanggal):
        return dt.date(v.tahun, v.bulan, v.hari)
    if isinstance(v, tomlku.Waktu):
        mikro = int((v.pecahan + "000000")[:6] or 0)
        return dt.time(v.jam, v.menit, v.detik, mikro)
    if isinstance(v, dict):
        return {k: ke_biasa(x) for k, x in v.items()}
    if isinstance(v, list):
        return [ke_biasa(x) for x in v]
    return v


def sama(a, b):
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and \
            all(sama(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and \
            all(sama(x, y) for x, y in zip(a, b))
    return a == b


if __name__ == "__main__":
    lulus, total, gagal, dilewati = jalankan()
    print("manifes penuh: %d/%d (dilewati %d)"
          % (lulus, total, len(dilewati)))
    for rel, pesan in gagal:
        print(" GAGAL %s — %s" % (rel, pesan[:120]))
    assert lulus == total
    # diferensial tomllib pada semua valid manifes
    entri = [l.strip() for l in open(MANIFES) if l.strip()]
    cek = 0
    for rel in entri:
        if not rel.startswith("valid/") or \
                not rel.endswith(".toml"):
            continue
        mentah = open(os.path.join(DIR_UJI, rel),
                      "rb").read()
        harap = tomllib.loads(mentah.decode("utf-8"))
        milik = ke_biasa(tomlku.muat(mentah))
        assert sama(milik, harap), "beda tomllib: %s" % rel
        cek += 1
    print("diferensial tomllib: %d/%d" % (cek, cek))
    print("LULUS — manifes 1.0.0 penuh")
