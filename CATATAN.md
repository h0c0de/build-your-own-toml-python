# CATATAN — Build 24: Parser TOML

Satu halaman per irisan: konsep inti + temuan.
Wasit: manifes `files-toml-1.0.0` dari toml-test
resmi (commit 96fd0884) — 709 uji terhitung,
8 dilewati terbuka (7 berkas invalid/encoding
berisi byte rusak yang ditolak konektor GitHub
saat pengunduhan + 1 berkas `.multi`).

## Irisan 1 — Skalar & kunci (227/227)

**Konsep.** Nilai skalar TOML tampak sederhana
sampai detailnya dibaca: garis bawah pada angka
hanya sah *di antara* digit; integer desimal tak
boleh berpangkat nol di depan; hex/oct/bin tidak
bertanda dan tetap terikat rentang 64-bit; float
wajib punya bagian bulat yang sah dan pecahan/
eksponen yang lengkap (`.5` dan `5.` bukan float).
Kunci bare hanyalah `[A-Za-z0-9_-]` — kunci angka
murni seperti `1234` adalah kunci string biasa.

**Temuan.** Pembanding harness-nya sendiri yang
pertama kali tertipu: node JSON resmi berbentuk
`{"type": ..., "value": ...}` bertabrakan dengan
tabel sah yang punya kunci bernama `type`. Daun
resmi dikenali dari pasangan persis dua kunci itu
dengan `type` berupa string — bukan dari keberadaan
kunci `type` saja.

## Irisan 2 — String multi-baris & datetime (111/111)

**Konsep.** String multi-baris membuang satu
newline pertama, mengizinkan kutip 1–2 di isi, dan
mengenal line-ending backslash yang memangkas
semua whitespace (termasuk newline) sesudahnya.
Datetime adalah empat bentuk RFC 3339: offset,
lokal, tanggal saja, waktu saja — dengan pemisah
`T`, `t`, atau satu spasi, dan pecahan detik
berdigit bebas.

**Temuan.** Dua hal. (1) Pecahan detik disimpan
sebagai string digit mentah: memaksakannya ke
`datetime` Python akan membuang presisi di atas
6 digit yang memang diizinkan spek dan diuji
suite. (2) Run kutip ≥6 di string multi-baris:
grammar hanya memberi tempat bagi paling banyak
2 kutip isi tepat sebelum penutup — run 6 menutup
string di kutip kelima dan menyisakan galat,
bukan menghasilkan 3 kutip isi.

## Irisan 3 — Array & inline table (94/94)

**Konsep.** Array boleh berisi campuran tipe
(aturan 1.0), bersarang, berkomentar di sela
nilainya, dan berkoma menggantung. Inline table
adalah dunia sebaliknya: satu baris, tanpa koma
menggantung, dan *beku* — begitu ditulis, tidak
ada header atau kunci bertitik dari luar yang
boleh menambah isinya.

**Temuan.** Komentar di dalam array adalah
satu-satunya tempat selain akhir baris di mana
`#` boleh muncul di tengah ekspresi — pengurai
array membutuhkan mode lewati-ruang sendiri yang
menelan whitespace + newline + komentar sekaligus,
berbeda dari konteks lain yang ketat per baris.

## Irisan 4 — Semantik tabel (237/237)

**Konsep.** Separuh TOML adalah hukum namespace:
tabel implisit (perantara header) boleh
didefinisikan belakangan; tabel header tidak
boleh dua kali; tabel hasil kunci bertitik tidak
boleh dijadikan target header tetapi boleh
ditumbuhi sub-tabel baru; kunci bertitik dari
konteks asing tidak boleh menembus tabel yang
sudah terdefinisi header/AOT (isu #846); `[t]`
di atas `[[t]]` terlarang sementara `[t.sub]`
menempel pada elemen terakhir AOT.

**Temuan.** Implementasinya menjadi jernih begitu
tiap tabel membawa *jenis kelahirannya*
(akar/implisit/header/titik/inline) sebagai data:
semua aturan di atas adalah pemeriksaan jenis
pada saat definisi atau lintasan, bukan tumpukan
kasus khusus. Contoh spek `[fruit.apple.texture]`
adalah bukti penentunya — ia membatalkan aturan
"header tak boleh melintasi tabel titik" yang
sempat kutulis dan menggantinya dengan perbedaan
target-vs-lintasan.

## Irisan 5 — Manifes penuh + tomllib (709/709, 208/208)

**Konsep.** Skor akhir diukur dua kali dengan dua
wasit yang tidak berhubungan: suite resmi
(dibandingkan semantik — float dari nilai, bukan
string; pecahan detik dinormalkan per grup tiga
digit mengikuti encoder referensi; NaN disamakan
dengan NaN) dan `tomllib` pustaka standar sebagai
diferensial independen pada semua kasus valid.

**Temuan.** Skor pertama 700/917 menipu dua kali:
manifes mencantumkan berkas `.json` pendamping
sebagai entri (bukan uji), dan total jujurnya
adalah 709. Pelajaran yang sama dengan build
sebelumnya — baca manifesnya, bukan asumsi tentang
manifesnya. Delapan berkas yang dilewati dicatat
terbuka di RENCANA: tujuh berkas encoding dengan
byte UTF-8/UTF-16 rusak yang ditolak konektor
GitHub (SHA blob-nya tercatat di arsip referensi)
dan satu berkas format `.multi`.
