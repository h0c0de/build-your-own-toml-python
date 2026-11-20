"""Irisan 1 — nilai skalar & kunci.

Kelompok suite: string dasar, key, integer, float,
bool (valid dibandingkan semantik, invalid ditolak).
"""
from uji_bersama import jalankan

KELOMPOK = ["string/basic", "string/quoted",
            "string/empty", "valid/key/", "invalid/key/",
            "integer/", "float/", "bool/"]

if __name__ == "__main__":
    lulus, total, gagal, _ = jalankan(KELOMPOK)
    print("irisan 1: %d/%d" % (lulus, total))
    for rel, pesan in gagal:
        print(" GAGAL %s — %s" % (rel, pesan[:120]))
    assert lulus == total
    print("LULUS")
