"""Irisan 4 — semantik tabel: header, AOT, kunci
bertitik, aturan duplikat/tertutup/beku, contoh spek.
"""
from uji_bersama import jalankan

KELOMPOK = ["table/", "spec-1.0.0/", "spec-1.1.0/",
            "example", "hard_example", "valid/local",
            "invalid/local"]

if __name__ == "__main__":
    lulus, total, gagal, _ = jalankan(KELOMPOK)
    print("irisan 4: %d/%d" % (lulus, total))
    for rel, pesan in gagal:
        print(" GAGAL %s — %s" % (rel, pesan[:120]))
    assert lulus == total
    print("LULUS")
