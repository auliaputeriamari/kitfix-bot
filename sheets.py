import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]

def get_client():
    creds_json = os.environ["GOOGLE_CREDENTIALS_JSON"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def get_sheet(sheet_name):
    client = get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        for ws in spreadsheet.worksheets():
            if ws.title.strip().upper() == sheet_name.strip().upper():
                return ws
        available = [ws.title for ws in spreadsheet.worksheets()]
        raise Exception(f"Sheet tidak ditemukan. Ada: {available}")

def find_next_empty_row_by_col(ws, col_index, start_row):
    """
    Cari baris kosong pertama berdasarkan kolom tertentu (1-indexed),
    mulai dari start_row.
    """
    values = ws.col_values(col_index)
    for i, val in enumerate(values[start_row - 1:], start=start_row):
        if not str(val).strip():
            return i
    return len(values) + 1

def rp(value):
    try:
        return int(str(value).replace(",", "").replace(".", "").strip())
    except (ValueError, TypeError):
        return 0

# PEMASUKAN HARIAN
# Row 1: judul, Row 2: nama toko, Row 3: kosong, Row 4: header kolom
# Data mulai baris 5, kolom A = Tanggal (tidak ada nomor urut)
def append_pemasukan(data):
    ws = get_sheet("PEMASUKAN HARIAN")
    # Cari baris kosong di kolom A (Tanggal), mulai baris 5
    row = find_next_empty_row_by_col(ws, col_index=1, start_row=5)
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

# PENGELUARAN
# Row 4: header, Row 5+: data dengan nomor urut di kolom A (sudah terisi 1-50)
# Cari baris kosong di kolom B (Tanggal), mulai baris 5
def append_pengeluaran(data):
    ws = get_sheet("PENGELUARAN")
    row = find_next_empty_row_by_col(ws, col_index=2, start_row=5)
    ws.update(
        f"B{row}:E{row}",
        [[
            data.get("Tanggal", ""),
            data.get("Kategori Pengeluaran", ""),
            rp(data.get("Nominal (Rp)", 0)),
            data.get("Metode Bayar", ""),
        ]],
        value_input_option="USER_ENTERED"
    )

# KAME → KITFIX
# Row 5: header, Row 6+: data dengan nomor urut di kolom A (sudah terisi)
# Cari baris kosong di kolom B (Tgl Masuk KAME), mulai baris 6
def append_kame_kitfix(data):
    ws = get_sheet("KAME → KITFIX")
    row = find_next_empty_row_by_col(ws, col_index=2, start_row=6)
    ws.update(
        f"B{row}:I{row}",
        [[
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

# KITFIX → KAME
# Row 5: header, Row 6+: data dengan nomor urut di kolom A (sudah terisi)
# Cari baris kosong di kolom B (Tgl Selesai), mulai baris 6
def append_kitfix_kame(data):
    ws = get_sheet("KITFIX → KAME")
    row = find_next_empty_row_by_col(ws, col_index=2, start_row=6)
    ws.update(
        f"B{row}:H{row}",
        [[
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
