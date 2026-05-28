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
    # Coba exact match dulu, lalu case-insensitive
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        # Coba cari nama yang mirip (case-insensitive)
        for ws in spreadsheet.worksheets():
            if ws.title.strip().upper() == sheet_name.strip().upper():
                return ws
        # Kalau tidak ketemu, tampilkan daftar sheet yang ada
        available = [ws.title for ws in spreadsheet.worksheets()]
        raise Exception(f"Sheet '{sheet_name}' tidak ditemukan. Sheet yang ada: {available}")

def find_next_empty_row(ws, start_row=6):
    col_a = ws.col_values(1)
    for i, val in enumerate(col_a[start_row - 1:], start=start_row):
        if not str(val).strip():
            return i
    return len(col_a) + 1

def rp(value):
    try:
        return int(str(value).replace(",", "").replace(".", "").strip())
    except (ValueError, TypeError):
        return 0

def append_pemasukan(data):
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

def append_pengeluaran(data):
    ws = get_sheet("PENGELUARAN")
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

    ws.update(
        f"A{row}:E{row}",
        [[
            last_no + 1,
            data.get("Tanggal", ""),
            data.get("Kategori Pengeluaran", ""),
            rp(data.get("Nominal (Rp)", 0)),
            data.get("Metode Bayar", ""),
        ]],
        value_input_option="USER_ENTERED"
    )

def append_kame_kitfix(data):
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

    ws.update(
        f"A{row}:I{row}",
        [[
            last_no + 1,
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

def append_kitfix_kame(data):
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

    ws.update(
        f"A{row}:H{row}",
        [[
            last_no + 1,
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
