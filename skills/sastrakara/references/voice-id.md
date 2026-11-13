# Voice reference: Indonesian

Read this when the document language is Indonesian. The Indonesian text below is sample
material: it shows the prose being written or checked.

## Voice

- "Anda" for the reader, "kita" for the team.
- Explain a term the first time it appears, in everyday words. Examples:
  - API: "jalur tempat aplikasi meminta data ke sistem lain, seperti loket pelayanan"
  - Cache: "salinan sementara agar halaman tidak perlu meminta data yang sama berulang kali"
  - Frontend: "bagian aplikasi yang Anda lihat dan klik di layar"
  - Database: "lemari arsip tempat sistem menyimpan catatannya"
- Analogies that work for flows: loket, papan informasi, arsip, kurir.
- A useful small table: "Informasi yang tampil · Sumber data · Seberapa sering diperbarui".

## Fixed strings

| Use | Text |
|---|---|
| Unknown, needs an answer | *(perlu konfirmasi tim teknis)* |
| Planned work | "rencana, belum tersedia" |
| Technical appendix heading | Lampiran Teknis |
| Technical appendix opener | "Bagian ini untuk tim teknis. Pembaca bisnis boleh melewatinya." (italic) |
| Key-terms heading | Istilah Penting |
| Limits heading | Batasan dan Hal yang Perlu Diperhatikan |
| Index columns | Dokumen · Untuk siapa · Tanggal · Format · Status |
| Index status | `Draf MD` · `DOCX` · `DOCX diedit manual` |
| Date | long form, for example "1 Oktober 2026" |
| Front matter | `lang: id-ID` |

## Reader check: what each question catches

The examples are Indonesian on purpose: they are samples of the text being checked.

**1. Would the reader miss it?**

| Found in the draft | Do this |
|---|---|
| "Seiring kemajuan teknologi saat ini, …" | Begin with the subject of the section |
| "Yuk, kita bahas satu per satu." | Go straight to the first item |
| "Dokumen ini akan menguraikan cara kerja laporan." | Describe how the report works |
| "Demikian penjelasan ini, semoga membantu." | End on the last fact |

**2. Where did it come from?**

| Found in the draft | Do this |
|---|---|
| "Fitur ini sangat disukai pengguna." | Delete; no file shows it |
| "Menurut banyak pihak, cara ini paling aman." | Name the source, or delete |
| "Nantinya layanan ini akan semakin lengkap." | Delete, or state a real plan labelled "rencana, belum tersedia" |

**3. Describe or decorate?**

| Found in the draft | Do this |
|---|---|
| "Sistem yang tangguh dan inovatif" | "Sistem tetap bisa dibuka saat satu server mati" |
| "Laporan dikirim setiap pagi" (the sender is known) | "Sistem mengirim laporan setiap pagi" |
| "Aplikasi mengerti apa yang Anda cari" | "Aplikasi menampilkan lima pencarian terakhir Anda" |
| "Sebagaimana diketahui bersama", "pada hakikatnya", "guna untuk" | Delete, or keep only "untuk" |

**4. Is the shape earned?**

| Found in the draft | Do this |
|---|---|
| Heading "Cara Kerjanya", first sentence "Cara kerjanya adalah sebagai berikut." | First sentence starts the explanation |
| "Lebih dari sekadar tabel, ini adalah pusat keputusan." | Say once what the table is used for |
| "cepat, mudah, dan aman" where only speed was shown | Keep what the code shows |
| Every important word in bold, emoji in headings | Bold for warnings only, no emoji |
| A paragraph that closes with "Karena data yang baik adalah awal keputusan yang baik." | Stop at the last fact |
