"""Irisan 3 — array & inline table."""
from uji_bersama import jalankan

KELOMPOK = ["array/", "inline-table/"]

if __name__ == "__main__":
    lulus, total, gagal, _ = jalankan(KELOMPOK)
    print("irisan 3: %d/%d" % (lulus, total))
    for rel, pesan in gagal:
        print(" GAGAL %s — %s" % (rel, pesan[:120]))
    assert lulus == total
    print("LULUS")
