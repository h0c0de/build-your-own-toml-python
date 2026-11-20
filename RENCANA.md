# RENCANA — Build 24: Parser TOML

Sumber: **Spesifikasi TOML v1.0.0** (toml.io) sebagai
panduan + **toml-test** resmi (toml-lang/toml-test,
commit 96fd0884) sebagai wasit — pola yang sama
dengan build 22: spesifikasinya sendiri yang dibaca,
baterai ujinya yang menghakimi.

Bukti emas pra-kode: manifes `files-toml-1.0.0` pada
suite resmi memuat **925 entri — sesudah pendamping
`.json` dikeluarkan, 717 berkas uji: 209 valid
(208 `.toml` terhitung + 1 `.multi` dilewati) dan
508 invalid (501 terhitung + 7 encoding tak
terunduh)**; 1055 dari 1063 berkas suite terunduh
dan terverifikasi SHA blob-nya (8 berkas
invalid/encoding berisi byte UTF-8 rusak yang ditolak
konektor GitHub — dicatat sebagai pengecualian jujur
di harness, bukan disembunyikan).

## Lingkup

MASUK:
- Dokumen penuh TOML 1.0.0: keyval, header tabel
  `[ ]`, header array-of-tables `[[ ]]`, kunci
  bertitik, kunci bare/terkutip.
- Semua nilai: string basic/literal satu & multi
  baris (escape, \u/\U, line-ending backslash),
  integer (dec/hex/oct/bin + garis bawah, rentang
  64-bit), float (eksponen, inf, nan), boolean,
  datetime RFC 3339 (offset, lokal, tanggal, waktu —
  pecahan detik presisi penuh), array (campuran,
  bersarang, komentar di dalamnya), inline table.
- Semantik namespace persis spek: kunci duplikat,
  tabel implisit vs terdefinisi, tabel hasil kunci
  bertitik tertutup untuk header, inline table beku,
  AOT menempel pada elemen terakhir.
- Penolakan yang benar untuk 501 kasus invalid
  terhitung (508 berkas invalid di manifes, 7
  encoding tak terunduh dilewati terbuka).

DILUAR (tercatat):
- TOML 1.1 (newline di inline table, escape \e, dsb.)
  — manifes 1.1.0 tersedia di suite tapi bukan target.
- Satu berkas valid `.multi` (numeric) — format
  multi-dokumen toml-test, dilewati dengan catatan.
- Penulis/serializer TOML (parser saja).
- Pesan galat berposisi baris/kolom (galat bertipe
  saja, dengan offset).

## Irisan

- [x] Irisan 1 — Nilai skalar: string satu baris,
  angka, boolean + kunci & keyval dasar.
- [x] Irisan 2 — String multi-baris + datetime.
- [x] Irisan 3 — Array + inline table.
- [x] Irisan 4 — Semantik tabel: header, AOT, kunci
  bertitik, aturan duplikat/tertutup/beku.
- [x] Irisan 5 — Final: seluruh manifes 1.0.0 (valid
  dibandingkan semantik ke JSON resmi; invalid wajib
  ditolak) + diferensial vs `tomllib` pada korpus
  valid.

## Pagar selesai

- [x] `uji_irisan1.py` … `uji_irisan5.py` hijau pada
  targetnya; skor manifes penuh tercetak jujur.
- [x] `CATATAN.md` satu halaman per irisan.
- [x] Repo GitHub publik
  `build-your-own-toml-python` terbit dan
  terverifikasi (SHA blob lokal == remote, halaman
  publik terbaca).
