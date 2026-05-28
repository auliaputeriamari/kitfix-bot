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
        raise Exception(f"Sheet '{sheet_name}' tidak ditemukan. Ada: {available}")

def find_next_empty_row(ws):
    """
    Cari baris kosong pertama di kolom A, mulai dari baris 2.
    Lewati baris header (yang isinya teks seperti 'Tanggal', 'No.', dll).
    """
    all_values = ws.col_values(1)
    header_keywords = ['no', 'tanggal', 'nama', 'laporan', 'toko', 'status',
                       'total', 'statistik', 'kolom', 'catat', 'ringkasan',
                       'tracking', 'tagihan', 'rekap']
    
    last_header_row = 1
    for i, val in enumerate(all_values, start=1):
        v = str(val).strip().lower()
        if any(kw in v for kw in header_keywords):
            last_header_row = i

    # Data mulai setelah baris header terakhir
    start_row = last_header_row + 1

    # Cari baris kosong pertama mulai dari sana
    for i, val in enumerate(all_values[start_row - 1:], start=start_row):
        if not str(val).strip():
            return i

    return len(all_values) + 1

def rp(value):
    try:
        return int(str(value).replace(",", "").replace(".", "").strip())
    except (ValueError, TypeError):
        return 0

def append_pemasukan(data):
    ws = get_sheet("PEMASUKAN HARIAN")
    row = find_next_empty_row(ws)
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
    row = find_next_empty_row(ws)

    existing = ws.col_values(1)
    last_no = 0
    for val in existing:
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
    row = find_next_empty_row(ws)

    existing = ws.col_values(1)
    last_no = 0
    for val in existing:
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
    row = find_next_empty_row(ws)

    existing = ws.col_values(1)
    last_no = 0
    for val in existing:
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
