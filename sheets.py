"""
sheets.py — Integrasi Google Sheets untuk bot KitFix.

Setiap fungsi menerima dict data dan append ke baris pertama yang kosong
di sheet yang sesuai dalam spreadsheet KitFix.
"""

import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]

# ─────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────

def get_client() -> gspread.Client:
    """Buat gspread client dari service account JSON di env var."""
    creds_json = os.environ["GOOGLE_CREDENTIALS_JSON"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def get_sheet(sheet_name: str) -> gspread.Worksheet:
    client = get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.worksheet(sheet_name)

# ─────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────

def find_next_empty_row(ws: gspread.Worksheet, start_row: int = 6) -> int:
    """
    Cari baris kosong pertama mulai dari start_row.
    Sheet KitFix punya header di baris 1-5, data mulai baris 6.
    """
    col_a = ws.col_values(1)  # ambil kolom A
    for i, val in enumerate(col_a[start_row - 1:], start=start_row):
        if not str(val).strip():
            return i
    # Kalau semua terisi, return baris setelah data terakhir
    return len(col_a) + 1

def rp(value: str) -> int:
    """Convert string angka ke int."""
    try:
        return int(str(value).replace(",", "").replace(".", "").strip())
    except ValueError:
        return 0

# ─────────────────────────────────────────────────
# PEMASUKAN HARIAN
# Sheet: "PEMASUKAN HARIAN"
# Kolom: Tanggal | Nama Pelanggan | Jasa | Harga (Rp) | Metode Bayar | Status | Catatan
# ─────────────────────────────────────────────────

def append_pemasukan(data: dict):
    ws = get_sheet("PEMASUKAN HARIAN")
    row = find_next_empty_row(ws, start_row=6)
    ws.update(
        f"A{row}:G{row}",
        [[
            data.get("Tanggal", ""),
            data.get("Nama Pelanggan", ""),
            data.get("Jasa", ""),
            rp(data.get("Harga (Rp)", 0)),
            data.get("Metode Bayar", ""),
            data.get("Status", ""),
            data.get("Catatan", ""),
        ]],
        value_input_option="USER_ENTERED"
    )

# ─────────────────────────────────────────────────
# PENGELUARAN
# Sheet: "PENGELUARAN"
# Kolom: No. | Tanggal | Kategori Pengeluaran | Nominal (Rp) | Metode Bayar
# ─────────────────────────────────────────────────

def append_pengeluaran(data: dict):
    ws = get_sheet("PENGELUARAN")
    row = find_next_empty_row(ws, start_row=6)

    # Hitung nomor urut
    existing = ws.col_values(1)
    last_no = 0
    for val in existing[5:]:
        try:
            n = int(val)
            if n > last_no:
                last_no = n
        except (ValueError, TypeError):
            pass
    new_no = last_no + 1

    ws.update(
        f"A{row}:E{row}",
        [[
            new_no,
            data.get("Tanggal", ""),
            data.get("Kategori Pengeluaran", ""),
            rp(data.get("Nominal (Rp)", 0)),
            data.get("Metode Bayar", ""),
        ]],
        value_input_option="USER_ENTERED"
    )

# ─────────────────────────────────────────────────
# KAME → KITFIX
# Sheet: "KAME → KITFIX"
# Kolom: No. | Tgl Masuk KAME | Nama Pelanggan | No. HP | Jenis Barang |
#         Keluhan / Pekerjaan | Harga Disepakati (Rp) | Status | Catatan
# ─────────────────────────────────────────────────

def append_kame_kitfix(data: dict):
    ws = get_sheet("KAME → KITFIX")
    row = find_next_empty_row(ws, start_row=6)

    existing = ws.col_values(1)
    last_no = 0
    for val in existing[5:]:
        try:
            n = int(val)
            if n > last_no:
                last_no = n
        except (ValueError, TypeError):
            pass
    new_no = last_no + 1

    ws.update(
        f"A{row}:I{row}",
        [[
            new_no,
            data.get("Tgl Masuk KAME", ""),
            data.get("Nama Pelanggan", ""),
            data.get("No. HP", ""),
            data.get("Jenis Barang", ""),
            data.get("Keluhan / Pekerjaan", ""),
            rp(data.get("Harga Disepakati (Rp)", 0)),
            data.get("Status", ""),
            data.get("Catatan", ""),
        ]],
        value_input_option="USER_ENTERED"
    )

# ─────────────────────────────────────────────────
# KITFIX → KAME
# Sheet: "KITFIX → KAME"
# Kolom: No. | Tgl Selesai di KitFix | Nama Pelanggan | Jenis Barang |
#         Pekerjaan yang Dilakukan | Biaya KitFix (Rp) | Status Pembayaran | Catatan
# ─────────────────────────────────────────────────

def append_kitfix_kame(data: dict):
    ws = get_sheet("KITFIX → KAME")
    row = find_next_empty_row(ws, start_row=6)

    existing = ws.col_values(1)
    last_no = 0
    for val in existing[5:]:
        try:
            n = int(val)
            if n > last_no:
                last_no = n
        except (ValueError, TypeError):
            pass
    new_no = last_no + 1

    ws.update(
        f"A{row}:H{row}",
        [[
            new_no,
            data.get("Tgl Selesai di KitFix", ""),
            data.get("Nama Pelanggan", ""),
            data.get("Jenis Barang", ""),
            data.get("Pekerjaan yang Dilakukan", ""),
            rp(data.get("Biaya KitFix (Rp)", 0)),
            data.get("Status Pembayaran", ""),
            data.get("Catatan", ""),
        ]],
        value_input_option="USER_ENTERED"
    )
