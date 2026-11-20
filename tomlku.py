"""Parser TOML v1.0.0.

Satu lintasan atas teks dengan pengurai kunci/nilai
rekursif. Nilai tanggal/waktu dikembalikan sebagai
kelas kecil berpresisi penuh (pecahan detik disimpan
sebagai string digit, karena TOML mengizinkan digit
sebanyak apa pun sedangkan datetime Python berhenti
di mikrodetik).
"""

import re


class GalatToml(Exception):
    """Dokumen TOML tidak sah."""


class Tanggal:
    __slots__ = ("tahun", "bulan", "hari")

    def __init__(self, tahun, bulan, hari):
        self.tahun, self.bulan, self.hari = tahun, bulan, hari

    def __eq__(self, lain):
        return isinstance(lain, Tanggal) and \
            (self.tahun, self.bulan, self.hari) == \
            (lain.tahun, lain.bulan, lain.hari)

    def __repr__(self):
        return "%04d-%02d-%02d" % (self.tahun, self.bulan,
                                   self.hari)


class Waktu:
    __slots__ = ("jam", "menit", "detik", "pecahan")

    def __init__(self, jam, menit, detik, pecahan=""):
        self.jam, self.menit = jam, menit
        self.detik, self.pecahan = detik, pecahan

    def __eq__(self, lain):
        return isinstance(lain, Waktu) and \
            (self.jam, self.menit, self.detik,
             self.pecahan) == (lain.jam, lain.menit,
                                lain.detik, lain.pecahan)

    def __repr__(self):
        dasar = "%02d:%02d:%02d" % (self.jam, self.menit,
                                    self.detik)
        return dasar + ("." + self.pecahan
                        if self.pecahan else "")


class TanggalWaktu:
    """offset = menit dari UTC, atau None bila lokal.
    `z` menandai penulisan Z (offset 0 via huruf Z)."""
    __slots__ = ("tanggal", "waktu", "offset")

    def __init__(self, tanggal, waktu, offset):
        self.tanggal, self.waktu = tanggal, waktu
        self.offset = offset

    def __eq__(self, lain):
        return isinstance(lain, TanggalWaktu) and \
            self.tanggal == lain.tanggal and \
            self.waktu == lain.waktu and \
            self.offset == lain.offset

    def __repr__(self):
        dasar = "%sT%s" % (self.tanggal, self.waktu)
        if self.offset is None:
            return dasar
        if self.offset == 0:
            return dasar + "Z"
        tanda = "+" if self.offset >= 0 else "-"
        o = abs(self.offset)
        return "%s%s%02d:%02d" % (dasar, tanda, o // 60,
                                  o % 60)


class Tabel:
    """Tabel TOML + jenis kelahirannya.

    jenis: 'akar', 'implisit' (perantara header),
    'header', 'titik' (dibuat kunci bertitik —
    tertutup untuk header), 'inline' (beku),
    'aot' menandai LIST array-of-tables lewat bendera
    terpisah pada pembungkus DaftarAot.
    """
    __slots__ = ("isi", "jenis")

    def __init__(self, jenis):
        self.isi = {}
        self.jenis = jenis


class DaftarAot(list):
    """List yang lahir dari [[header]] — boleh
    ditambah elemennya dan dilintasi ke elemen
    terakhir; list biasa (dari nilai array) tidak."""
    __slots__ = ()


_BARE = re.compile(r"[A-Za-z0-9_-]+")
_RE_INT_DEC = re.compile(r"[+-]?(0|[1-9](?:_?[0-9])*)\Z")
_RE_UNDERSCORE_OK = re.compile(r"[0-9A-Fa-f](?:_?[0-9A-Fa-f])*\Z")


def _cek_kontrol(c, konteks):
    """Karakter kontrol selain tab terlarang hampir
    di semua konteks TOML; DEL (0x7F) juga."""
    o = ord(c)
    if (o < 0x20 and c != "\t") or o == 0x7F:
        raise GalatToml("karakter kontrol di %s" % konteks)


class Pengurai:
    def __init__(self, teks):
        if isinstance(teks, bytes):
            try:
                teks = teks.decode("utf-8")
            except UnicodeDecodeError as e:
                raise GalatToml("bukan UTF-8 sah: %s" % e)
        self.s = teks
        self.i = 0
        self.n = len(teks)

    # ---------- primitif ----------
    def intip(self, geser=0):
        j = self.i + geser
        return self.s[j] if j < self.n else ""

    def galat(self, pesan):
        raise GalatToml("%s (offset %d)" % (pesan, self.i))

    def _ws(self):
        while self.intip() in (" ", "\t"):
            self.i += 1

    def _newline(self):
        """Konsumsi satu newline (LF atau CRLF)."""
        if self.intip() == "\n":
            self.i += 1
            return True
        if self.intip() == "\r" and self.intip(1) == "\n":
            self.i += 2
            return True
        return False

    def _komentar(self):
        # posisi di '#'
        self.i += 1
        while self.i < self.n and self.intip() not in ("\n", "\r"):
            c = self.intip()
            if c != "\t":
                _cek_kontrol(c, "komentar")
            self.i += 1

    def _akhir_baris(self):
        """Sesudah keyval/header: ws, komentar opsional,
        lalu newline atau EOF."""
        self._ws()
        if self.intip() == "#":
            self._komentar()
        if self.i >= self.n:
            return
        if not self._newline():
            self.galat("sisa tak terduga di akhir baris")

    # ---------- dokumen ----------
    def urai(self):
        akar = Tabel("akar")
        konteks = akar
        while True:
            self._ws()
            c = self.intip()
            if c == "":
                return _ke_dict_biasa(akar)
            if c == "#":
                self._komentar()
            elif c in ("\n", "\r"):
                if not self._newline():
                    self.galat("CR tanpa LF")
            elif c == "[":
                konteks = self._header(akar)
                self._akhir_baris()
            else:
                self._keyval(konteks)
                self._akhir_baris()

    def _header(self, akar):
        aot = self.intip(1) == "["
        self.i += 2 if aot else 1
        self._ws()
        jalur = self._kunci_bertitik()
        self._ws()
        if aot:
            if self.intip() != "]" or self.intip(1) != "]":
                self.galat("header AOT tanpa ]]")
            self.i += 2
            induk = self._lintasi(akar, jalur[:-1],
                                  untuk_header=True)
            nama = jalur[-1]
            node = induk.isi.get(nama)
            if node is None:
                node = DaftarAot()
                induk.isi[nama] = node
            if not isinstance(node, DaftarAot):
                self.galat("[[%s]] di atas bukan array tabel"
                           % nama)
            elemen = Tabel("header")
            node.append(elemen)
            return elemen
        if self.intip() != "]":
            self.galat("header tabel tanpa ]")
        self.i += 1
        induk = self._lintasi(akar, jalur[:-1],
                              untuk_header=True)
        nama = jalur[-1]
        node = induk.isi.get(nama)
        if node is None:
            node = Tabel("header")
            induk.isi[nama] = node
            return node
        if isinstance(node, DaftarAot):
            self.galat("[tabel] di atas array tabel")
        if isinstance(node, Tabel):
            if node.jenis == "implisit":
                node.jenis = "header"
                return node
            self.galat("tabel %s didefinisikan dua kali"
                       % nama)
        self.galat("header di atas nilai")

    def _lintasi(self, akar, jalur, untuk_header=False,
                 untuk_keyval=False):
        """Jalan menuruni jalur kunci dari akar,
        membuat tabel implisit/titik sesuai konteks."""
        node = akar
        for nama in jalur:
            anak = node.isi.get(nama)
            if anak is None:
                anak = Tabel("implisit" if untuk_header
                             else "titik")
                node.isi[nama] = anak
            elif isinstance(anak, DaftarAot):
                if not anak:
                    self.galat("AOT kosong")
                anak = anak[-1]
            elif isinstance(anak, Tabel):
                if anak.jenis == "inline":
                    self.galat("menembus inline table beku")
                # tabel 'titik' BOLEH dilintasi header:
                # yang terlarang hanya menjadikannya
                # target definisi (dicek di _header) —
                # sub-tabel baru di bawahnya sah
                # (contoh spek: [fruit.apple.texture]).
            else:
                self.galat("kunci menembus nilai")
            node = anak
        return node

    def _keyval(self, konteks):
        jalur = self._kunci_bertitik()
        self._ws()
        if self.intip() != "=":
            self.galat("keyval tanpa =")
        self.i += 1
        self._ws()
        nilai = self._nilai()
        induk = self._lintasi_dari(konteks, jalur[:-1])
        nama = jalur[-1]
        if nama in induk.isi:
            self.galat("kunci duplikat: %s" % nama)
        induk.isi[nama] = nilai

    def _lintasi_dari(self, konteks, jalur):
        """Lintasan kunci bertitik pada keyval.

        Aturan isu #846 spek: dari konteks keyval,
        kunci bertitik hanya boleh membuat tabel baru
        atau menuruni tabel 'titik'/'implisit' —
        menuruni tabel yang terdefinisi header, AOT,
        atau inline dari konteks lain tidak sah.
        """
        node = konteks
        for nama in jalur:
            anak = node.isi.get(nama)
            if anak is None:
                anak = Tabel("titik")
                node.isi[nama] = anak
            elif isinstance(anak, DaftarAot):
                self.galat("kunci bertitik menembus "
                           "array tabel")
            elif isinstance(anak, Tabel):
                if anak.jenis == "inline":
                    self.galat("menembus inline table beku")
                if anak.jenis not in ("titik", "implisit"):
                    self.galat("kunci bertitik menembus "
                               "tabel terdefinisi")
            else:
                self.galat("kunci menembus nilai")
            node = anak
        return node

    # ---------- kunci ----------
    def _kunci_bertitik(self):
        bagian = [self._kunci_satu()]
        while True:
            self._ws()
            if self.intip() != ".":
                return bagian
            self.i += 1
            self._ws()
            bagian.append(self._kunci_satu())

    def _kunci_satu(self):
        c = self.intip()
        if c == '"':
            return self._string_basic_satu()
        if c == "'":
            return self._string_literal_satu()
        m = _BARE.match(self.s, self.i)
        if not m:
            self.galat("kunci tidak sah")
        self.i = m.end()
        return m.group(0)

    # ---------- nilai ----------
    def _nilai(self):
        c = self.intip()
        if c == '"':
            if self.s[self.i:self.i + 3] == '"""':
                return self._string_basic_multi()
            return self._string_basic_satu()
        if c == "'":
            if self.s[self.i:self.i + 3] == "'''":
                return self._string_literal_multi()
            return self._string_literal_satu()
        if c == "[":
            return self._array()
        if c == "{":
            return self._inline_table()
        return self._skalar()

    # ---------- string ----------
    _ESCAPE = {"b": "\b", "t": "\t", "n": "\n", "f": "\f",
               "r": "\r", '"': '"', "\\": "\\"}

    def _escape(self):
        # posisi di backslash
        self.i += 1
        c = self.intip()
        if c in self._ESCAPE:
            self.i += 1
            return self._ESCAPE[c]
        if c in ("u", "U"):
            jumlah = 4 if c == "u" else 8
            digit = self.s[self.i + 1:self.i + 1 + jumlah]
            if len(digit) < jumlah or not all(
                    ch in "0123456789abcdefABCDEF"
                    for ch in digit):
                self.galat("escape unicode tak lengkap")
            titik = int(digit, 16)
            if titik > 0x10FFFF or 0xD800 <= titik <= 0xDFFF:
                self.galat("titik kode unicode tak sah")
            self.i += 1 + jumlah
            return chr(titik)
        self.galat("escape tidak dikenal: \\%s" % c)

    def _string_basic_satu(self):
        self.i += 1  # "
        keluar = []
        while True:
            c = self.intip()
            if c == "":
                self.galat("string basic tak ditutup")
            if c == '"':
                self.i += 1
                return "".join(keluar)
            if c == "\\":
                keluar.append(self._escape())
            elif c in ("\n", "\r"):
                self.galat("newline di string satu baris")
            else:
                _cek_kontrol(c, "string")
                keluar.append(c)
                self.i += 1

    def _string_literal_satu(self):
        self.i += 1  # '
        awal = self.i
        while True:
            c = self.intip()
            if c == "":
                self.galat("string literal tak ditutup")
            if c == "'":
                hasil = self.s[awal:self.i]
                self.i += 1
                return hasil
            if c in ("\n", "\r"):
                self.galat("newline di string literal")
            _cek_kontrol(c, "string literal")
            self.i += 1

    def _string_basic_multi(self):
        self.i += 3  # """
        self._newline()  # newline pertama dibuang
        keluar = []
        while True:
            c = self.intip()
            if c == "":
                self.galat("string multi tak ditutup")
            if c == '"':
                # run kutip: 1-2 = isi; 3-5 = (run-3) isi
                # + penutup; >=6 = 2 isi + penutup yang
                # memakan 5, sisanya jadi galat sintaks
                j = self.i
                while j < self.n and self.s[j] == '"':
                    j += 1
                run = j - self.i
                if run >= 3:
                    if run <= 5:
                        keluar.append('"' * (run - 3))
                        self.i += run
                    else:
                        keluar.append('""')
                        self.i += 5
                    return "".join(keluar)
                keluar.append('"' * run)
                self.i += run
            elif c == "\\":
                # line-ending backslash? backslash lalu
                # ws lalu newline -> pangkas semua ws
                j = self.i + 1
                while j < self.n and self.s[j] in (" ", "\t"):
                    j += 1
                if j < self.n and (self.s[j] == "\n" or
                                   (self.s[j] == "\r" and
                                    j + 1 < self.n and
                                    self.s[j + 1] == "\n")):
                    self.i = j
                    while True:
                        while self.intip() in (" ", "\t"):
                            self.i += 1
                        if not self._newline():
                            break
                else:
                    keluar.append(self._escape())
            elif c == "\r":
                if self.intip(1) == "\n":
                    keluar.append("\r\n")
                    self.i += 2
                else:
                    self.galat("CR tanpa LF di string")
            else:
                if c != "\n":
                    _cek_kontrol(c, "string multi")
                keluar.append(c)
                self.i += 1

    def _string_literal_multi(self):
        self.i += 3  # '''
        self._newline()
        keluar = []
        while True:
            c = self.intip()
            if c == "":
                self.galat("string literal multi tak ditutup")
            if c == "'":
                j = self.i
                while j < self.n and self.s[j] == "'":
                    j += 1
                run = j - self.i
                if run >= 3:
                    if run <= 5:
                        keluar.append("'" * (run - 3))
                        self.i += run
                    else:
                        keluar.append("''")
                        self.i += 5
                    return "".join(keluar)
                keluar.append("'" * run)
                self.i += run
            elif c == "\r":
                if self.intip(1) == "\n":
                    keluar.append("\r\n")
                    self.i += 2
                else:
                    self.galat("CR tanpa LF di string")
            else:
                if c != "\n":
                    _cek_kontrol(c, "string literal multi")
                keluar.append(c)
                self.i += 1

    # ---------- skalar: angka, boolean, datetime ----------
    _RE_TANGGAL = re.compile(
        r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
    _RE_WAKTU = re.compile(
        r"([0-9]{2}):([0-9]{2}):([0-9]{2})"
        r"(?:\.([0-9]+))?")

    def _buat_tanggal(self, m):
        import datetime as _dt
        y, bl, h = (int(m.group(1)), int(m.group(2)),
                    int(m.group(3)))
        try:
            _dt.date(y, bl, h)
        except ValueError:
            self.galat("tanggal tidak sah")
        return Tanggal(y, bl, h)

    def _buat_waktu(self, m):
        jam, men, det = (int(m.group(1)), int(m.group(2)),
                         int(m.group(3)))
        if jam > 23 or men > 59 or det > 59:
            self.galat("waktu tidak sah")
        return Waktu(jam, men, det, m.group(4) or "")

    def _skalar(self):
        s, i = self.s, self.i
        # datetime: tanggal penuh?
        m = self._RE_TANGGAL.match(s, i)
        if m and not (i > 0 and (s[i - 1].isdigit())):
            sesudah = s[m.end():m.end() + 1]
            # tanggal saja, atau diikuti T/t/spasi+waktu
            ikut = False
            if sesudah in ("T", "t"):
                ikut = True
            elif sesudah == " ":
                potong = s[m.end() + 1:m.end() + 9]
                ikut = bool(self._RE_WAKTU.match(potong))
            if ikut or not (sesudah.isdigit()
                            or sesudah == "-"):
                tanggal = self._buat_tanggal(m)
                self.i = m.end()
                if not ikut:
                    return tanggal
                if sesudah == " ":
                    self.i += 1
                else:
                    self.i += 1  # T/t
                mw = self._RE_WAKTU.match(self.s, self.i)
                if not mw:
                    self.galat("datetime tanpa waktu sah")
                waktu = self._buat_waktu(mw)
                self.i = mw.end()
                offset = None
                c = self.intip()
                if c in ("Z", "z"):
                    offset = 0
                    self.i += 1
                elif c in ("+", "-"):
                    tanda = 1 if c == "+" else -1
                    mo = re.match(r"([0-9]{2}):([0-9]{2})",
                                  self.s[self.i + 1:])
                    if not mo:
                        self.galat("offset datetime tak sah")
                    oj, om = int(mo.group(1)), int(mo.group(2))
                    if oj > 23 or om > 59:
                        self.galat("offset di luar rentang")
                    offset = tanda * (oj * 60 + om)
                    self.i += 1 + mo.end()
                return TanggalWaktu(tanggal, waktu, offset)
        # waktu lokal?
        mw = self._RE_WAKTU.match(s, i)
        if mw:
            self.i = mw.end()
            return self._buat_waktu(mw)
        # boolean
        for kata, nilai in (("true", True), ("false", False)):
            if s.startswith(kata, i):
                self.i += len(kata)
                return nilai
        return self._angka()

    def _angka(self):
        s, i = self.s, self.i
        j = i
        if j < self.n and s[j] in "+-":
            j += 1
        # inf / nan
        for kata in ("inf", "nan"):
            if s.startswith(kata, j):
                self.i = j + 3
                nilai = float(kata)
                return -nilai if s[i] == "-" else nilai
        # berbasis: 0x / 0o / 0b (tanpa tanda)
        if s.startswith(("0x", "0o", "0b"), i):
            awalan = s[i + 1]
            digitset = {  # noqa: E501
                "x": "0123456789abcdefABCDEF",
                "o": "01234567", "b": "01"}[awalan]
            basis = {"x": 16, "o": 8, "b": 2}[awalan]
            m = re.match(r"[0-9A-Za-z_]+", s[i + 2:])
            mentah = m.group(0) if m else ""
            if not mentah or not _RE_UNDERSCORE_OK.match(
                    mentah) or any(ch not in digitset
                                   for ch in mentah
                                   if ch != "_"):
                self.galat("digit berbasis tidak sah")
            self.i = i + 2 + len(mentah)
            nilai = int(mentah.replace("_", ""), basis)
            if nilai > 0x7FFFFFFFFFFFFFFF:
                self.galat("integer di luar 64-bit")
            return nilai
        # desimal / float: kumpulkan token angka
        m = re.match(r"[+-]?[0-9][0-9_]*"
                     r"(?:\.[0-9_]+)?"
                     r"(?:[eE][+-]?[0-9][0-9_]*)?", s[i:])
        if not m:
            self.galat("nilai tidak dikenal")
        token = m.group(0)
        self.i += len(token)
        bersih = token.replace("_", "")
        if "." in token or "e" in token or "E" in token:
            # validasi ketat bentuk float
            if not re.fullmatch(
                    r"[+-]?(0|[1-9](?:_?[0-9])*)"
                    r"(?:\.[0-9](?:_?[0-9])*)?"
                    r"(?:[eE][+-]?[0-9](?:_?[0-9])*)?",
                    token) or (
                    "." not in token and "e" not in token
                    and "E" not in token):
                self.galat("float tidak sah")
            if "." not in token and not re.search(
                    r"[eE][+-]?[0-9]", token):
                self.galat("float tidak sah")
            return float(bersih)
        if not _RE_INT_DEC.fullmatch(token):
            self.galat("integer tidak sah")
        nilai = int(bersih)
        if not (-0x8000000000000000 <= nilai
                <= 0x7FFFFFFFFFFFFFFF):
            self.galat("integer di luar 64-bit")
        return nilai

    # ---------- array & inline table ----------
    def _lewati_ruang_array(self):
        while True:
            self._ws()
            if self.intip() == "#":
                self._komentar()
            if not self._newline() and \
                    self.intip() not in (" ", "\t", "#"):
                return

    def _array(self):
        self.i += 1  # [
        hasil = []
        while True:
            self._lewati_ruang_array()
            if self.intip() == "]":
                self.i += 1
                return hasil
            if self.i >= self.n:
                self.galat("array tak ditutup")
            hasil.append(self._nilai())
            self._lewati_ruang_array()
            c = self.intip()
            if c == ",":
                self.i += 1
            elif c == "]":
                self.i += 1
                return hasil
            else:
                self.galat("array tanpa koma")

    def _inline_table(self):
        self.i += 1  # {
        tabel = Tabel("inline")
        self._ws()
        if self.intip() == "}":
            self.i += 1
            return tabel
        while True:
            if self.intip() in ("\n", "\r"):
                self.galat("newline di inline table (1.0)")
            jalur = self._kunci_bertitik()
            self._ws()
            if self.intip() != "=":
                self.galat("inline table tanpa =")
            self.i += 1
            self._ws()
            if self.intip() in ("\n", "\r"):
                self.galat("newline di inline table (1.0)")
            nilai = self._nilai()
            induk = self._lintasi_dari(tabel, jalur[:-1])
            nama = jalur[-1]
            if nama in induk.isi:
                self.galat("kunci duplikat di inline table")
            induk.isi[nama] = nilai
            self._ws()
            c = self.intip()
            if c == ",":
                self.i += 1
                self._ws()
                if self.intip() == "}":
                    self.galat("koma menggantung inline table")
            elif c == "}":
                self.i += 1
                return tabel
            else:
                self.galat("inline table tanpa koma/tutup")


def _ke_dict_biasa(node):
    if isinstance(node, Tabel):
        return {k: _ke_dict_biasa(v)
                for k, v in node.isi.items()}
    if isinstance(node, list):
        return [_ke_dict_biasa(v) for v in node]
    return node


def muat(teks):
    """Parse dokumen TOML (str atau bytes) -> dict."""
    return Pengurai(teks).urai()
