"""
TOPSIS Web App - versi web dari program Kelompok 3
====================================================
Logika perhitungan mengikuti persis punya program "kelompok_3_topsis.py"
(nama alternatif & kriteria custom, tipe kriteria "keuntungan"/"biaya"),
cuma tampilannya dipindah dari terminal ke web (HTML + API Flask).

Jalankan:
    pip install flask
    python app.py
lalu buka http://127.0.0.1:5000
"""

import math
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)


def cetak_matrik_blocks(judul, alternatif, kriteria, M, blocks):
    """Menambahkan satu tabel matriks ke daftar blocks, format sama seperti cetak_matrik() di versi terminal."""
    blocks.append({
        "type": "table",
        "title": judul,
        "header": kriteria,
        "rows": [{"label": alternatif[i], "values": [round(float(v), 4) for v in M[i]]}
                 for i in range(len(alternatif))],
    })


def hitung_topsis(alternatif, kriteria, tipe_krit, bobot, matrik):
    """
    Persis mengikuti alur kelompok_3_topsis.py:
    - nilai_rij  : penyebut normalisasi per kolom kriteria
    - matrik_R   : matriks ternormalisasi
    - matrik_Y   : matriks ternormalisasi terbobot
    - Y_plus/Y_min : solusi ideal positif/negatif (berdasar tipe "keuntungan"/"biaya")
    - D_plus/D_min : jarak tiap alternatif ke solusi ideal
    - V          : nilai preferensi
    """
    alt = len(alternatif)
    krit = len(kriteria)
    blocks = []

    def teks(t):
        blocks.append({"type": "text", "content": t})

    # ---------------- TABEL AWAL ----------------
    blocks.append({"type": "heading", "content": "Tabel Awal"})
    cetak_matrik_blocks("Matriks Keputusan", alternatif, kriteria, matrik, blocks)
    teks(f"Bobot: {bobot}")
    teks("Tipe kriteria: " + ", ".join(f"{kriteria[i]}={tipe_krit[i]}" for i in range(krit)))

    # ---------------- NORMALISASI (nilai_rij & matrik_R) ----------------
    blocks.append({"type": "heading", "content": "Normalisasi -> Matrik (R)"})
    teks("Rumus: rij = xij / akar( jumlah kuadrat nilai di kolom kriteria j )")

    nilai_rij = []
    for i in range(krit):
        jumlah_kuadrat = sum(matrik[j][i] ** 2 for j in range(alt))
        akar = math.sqrt(jumlah_kuadrat)
        nilai_rij.append(akar)
        detail = " + ".join(f"{matrik[j][i]}^2" for j in range(alt))
        teks(f"Kriteria {kriteria[i]}: akar({detail}) = akar({jumlah_kuadrat:.4f}) = {akar:.4f}")

    matrik_R = [[matrik[i][j] / nilai_rij[j] for j in range(krit)] for i in range(alt)]

    for i in range(alt):
        detail = " ; ".join(
            f"r{i+1}{j+1} = {matrik[i][j]}/{nilai_rij[j]:.4f} = {matrik_R[i][j]:.4f}"
            for j in range(krit)
        )
        teks(f"{alternatif[i]}: " + detail)

    cetak_matrik_blocks("Hasil Matrik (R)", alternatif, kriteria, matrik_R, blocks)

    # ---------------- PEMBOBOTAN (matrik_Y) ----------------
    blocks.append({"type": "heading", "content": "Pembobotan -> Matrik (Y)"})
    teks("Rumus: yij = rij x bobot_j")

    matrik_Y = [[matrik_R[i][j] * bobot[j] for j in range(krit)] for i in range(alt)]

    for i in range(alt):
        detail = " ; ".join(
            f"y{i+1}{j+1} = {matrik_R[i][j]:.4f} x {bobot[j]} = {matrik_Y[i][j]:.4f}"
            for j in range(krit)
        )
        teks(f"{alternatif[i]}: " + detail)

    cetak_matrik_blocks("Hasil Matrik (Y)", alternatif, kriteria, matrik_Y, blocks)

    # ---------------- SOLUSI IDEAL ----------------
    blocks.append({"type": "heading", "content": "Solusi Ideal"})
    teks("keuntungan -> Y+ = nilai MAX kolom , Y- = nilai MIN kolom")
    teks("biaya      -> Y+ = nilai MIN kolom , Y- = nilai MAX kolom")

    Y_plus = [0.0] * krit
    Y_min = [0.0] * krit
    for i in range(krit):
        kolom = [matrik_Y[j][i] for j in range(alt)]
        if tipe_krit[i] == "keuntungan":
            Y_plus[i] = max(kolom)
            Y_min[i] = min(kolom)
        else:
            Y_plus[i] = min(kolom)
            Y_min[i] = max(kolom)
        teks(f"{kriteria[i]} ({tipe_krit[i]}): Y+ = {Y_plus[i]:.4f} ; Y- = {Y_min[i]:.4f} "
             f"(dari kolom {[round(v,4) for v in kolom]})")

    # ---------------- JARAK ALTERNATIF ----------------
    blocks.append({"type": "heading", "content": "Jarak Alternatif"})
    teks("Rumus: D+ = akar(sum (yij - Y+j)^2)  ;  D- = akar(sum (yij - Y-j)^2)")

    D_plus = []
    D_min = []
    for i in range(alt):
        detail_plus = []
        detail_min = []
        for j in range(krit):
            sp = matrik_Y[i][j] - Y_plus[j]
            sm = matrik_Y[i][j] - Y_min[j]
            detail_plus.append(f"({matrik_Y[i][j]:.4f}-{Y_plus[j]:.4f})^2={sp**2:.4f}")
            detail_min.append(f"({matrik_Y[i][j]:.4f}-{Y_min[j]:.4f})^2={sm**2:.4f}")

        d_plus = math.sqrt(sum((matrik_Y[i][j] - Y_plus[j]) ** 2 for j in range(krit)))
        d_min = math.sqrt(sum((matrik_Y[i][j] - Y_min[j]) ** 2 for j in range(krit)))
        D_plus.append(d_plus)
        D_min.append(d_min)

        teks(f"{alternatif[i]} - D+: " + " + ".join(detail_plus) + f" -> akar(...) = {d_plus:.4f}")
        teks(f"{alternatif[i]} - D-: " + " + ".join(detail_min) + f" -> akar(...) = {d_min:.4f}")

    # ---------------- NILAI PREFERENSI ----------------
    blocks.append({"type": "heading", "content": "Nilai Preferensi"})
    teks("Rumus: Vi = D-i / (D-i + D+i)")

    V = [D_min[i] / (D_min[i] + D_plus[i]) for i in range(alt)]
    for i in range(alt):
        teks(f"V({alternatif[i]}) = {D_min[i]:.4f} / ({D_min[i]:.4f}+{D_plus[i]:.4f}) = {V[i]:.4f}")

    # ---------------- RINGKASAN ----------------
    urutan = sorted(range(alt), key=lambda i: V[i], reverse=True)
    ringkasan = {
        "header": ["D+", "D-", "V"],
        "rows": [{"label": alternatif[i], "values": [round(D_plus[i], 4), round(D_min[i], 4), round(V[i], 4)]}
                 for i in range(alt)],
        "ranking": [{"peringkat": p + 1, "nama": alternatif[idx], "vi": round(V[idx], 4)}
                    for p, idx in enumerate(urutan)],
        "terbaik": alternatif[urutan[0]],
    }

    return blocks, ringkasan


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/topsis", methods=["POST"])
def api_topsis():
    data = request.get_json(force=True)
    try:
        alternatif = data["alternatif"]
        kriteria = data["kriteria"]
        tipe = data["tipe"]          # list "keuntungan" / "biaya"
        bobot = data["bobot"]
        matrik = data["matrik"]

        if len(kriteria) != len(bobot) or len(kriteria) != len(tipe):
            return jsonify({"error": "Jumlah kriteria, bobot, dan tipe harus sama."}), 400
        for baris in matrik:
            if len(baris) != len(kriteria):
                return jsonify({"error": "Jumlah kolom tiap baris harus sama dengan jumlah kriteria."}), 400
        for t in tipe:
            if t not in ("keuntungan", "biaya"):
                return jsonify({"error": "Tipe kriteria harus 'keuntungan' atau 'biaya'."}), 400

        blocks, ringkasan = hitung_topsis(alternatif, kriteria, tipe, bobot, matrik)
        return jsonify({"blocks": blocks, "ringkasan": ringkasan})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True)
