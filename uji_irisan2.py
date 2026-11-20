"""Irisan 2 — string multi-baris & datetime."""
from uji_bersama import jalankan

KELOMPOK = ["multiline", "datetime/", "valid/string/raw",
            "valid/string/escapes", "valid/string/escape",
            "valid/comment/"]

if __name__ == "__main__":
    lulus, total, gagal, _ = jalankan(KELOMPOK)
    print("irisan 2: %d/%d" % (lulus, total))
    for rel, pesan in gagal:
        print(" GAGAL %s — %s" % (rel, pesan[:120]))
    assert lulus == total
    print("LULUS")
