# Build Your Own — Parser TOML

Parser **TOML v1.0.0** lengkap dalam Python murni,
dibangun mengikuti spesifikasinya dan dibuktikan
dengan baterai uji resmi bahasa itu sendiri:
**toml-test** (toml-lang/toml-test) manifes
`files-toml-1.0.0` — **709/709 uji terhitung lulus**
(208 berkas valid dibandingkan semantik ke JSON
resmi; 501 berkas invalid wajib ditolak; 8 berkas
dilewati terbuka — 7 berkas encoding rusak yang
ditolak konektor GitHub dan 1 berkas format
`.multi`), plus diferensial penuh melawan `tomllib`
dari pustaka standar pada semua 208 kasus valid
berkas `.toml`: **208/208 identik**.

## Isi

| Berkas | Isi |
| --- | --- |
| `tomlku.py` | Parsernya: dokumen, header tabel/AOT, kunci bertitik, semua nilai, semantik namespace spek |
| `uji_bersama.py` | Mesin uji manifes toml-test dengan pembanding semantik |
| `uji_irisan1.py` … `uji_irisan5.py` | Uji per irisan; irisan 5 = manifes penuh + diferensial tomllib |

Suite ujinya sendiri tidak disertakan (ia hidup di
repo toml-lang/toml-test, commit `96fd0884`); harness
membacanya dari folder referensi lokal `../toml-ref`.

## Memakai

```python
from tomlku import muat

doc = muat("""
judul = "Latihan"

[pemilik]
nama = "Vero"
sejak = 2003-01-01
""")
assert doc["pemilik"]["sejak"].tahun == 2003
```

Nilai tanggal/waktu dikembalikan sebagai kelas
kecil (`Tanggal`, `Waktu`, `TanggalWaktu`) yang
menyimpan pecahan detik sebagai string digit —
TOML mengizinkan digit pecahan sebanyak apa pun,
sedangkan `datetime` Python berhenti di mikrodetik.

## Tiga aturan yang menentukan

1. **Jenis kelahiran tabel adalah hukumnya.**
   Tabel yang lahir dari header `[a]`, dari kunci
   bertitik `a.b = 1`, dari inline `{...}`, atau
   sebagai perantara implisit header lain, masing-
   masing punya hak yang berbeda: yang implisit
   boleh didefinisikan kemudian; yang dari kunci
   bertitik tidak boleh dijadikan target header —
   tetapi sub-tabel BARU di bawahnya boleh
   (`[fruit.apple.texture]` pada contoh spek sah,
   `[fruit.apple]` tidak).

2. **Kunci bertitik tidak menembus tabel asing**
   (keputusan spek, isu #846): sesudah `[a.b.c]`
   terdefinisi, menulis `b.c.t = ...` dari konteks
   `[a]` ditolak — walau secara logika "tinggal
   menambah". Kunci bertitik hanya boleh membuat
   tabel baru atau menuruni tabel hasil kunci
   bertitik/implisit.

3. **Array tabel menempel pada elemen terakhir.**
   `[tabel]` sesudah `[[tabel]]` adalah definisi
   ganda yang terlarang, tetapi `[tabel.sub]` sah —
   ia menempel pada elemen terakhir `[[tabel]]`.
   Perbedaan antara *target* dan *lintasan* ini
   adalah separuh dari semantik TOML.

## Temuan paling menarik

Kegagalan terakhir yang gugur bukan soal sintaks
melainkan soal kutip: di dalam string multi-baris,
run 6+ tanda kutip bukanlah "3 isi + penutup" —
grammar-nya hanya mengizinkan paling banyak 2 kutip
isi tepat sebelum penutup 3, jadi run 6 berarti
string berakhir di kutip ke-5 dan sisanya adalah
galat. Cerita lengkapnya di `CATATAN.md`.

## Lisensi

Kode: MIT. Spesifikasi TOML © kontributor TOML;
suite toml-test © kontributor toml-test (BSD).
