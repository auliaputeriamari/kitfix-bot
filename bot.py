import os
import re
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from sheets import append_pemasukan, append_pengeluaran

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))

# ─────────────────────────────────────────────────
# GUARDS
# ─────────────────────────────────────────────────

def is_allowed(update: Update) -> bool:
    if ALLOWED_USER_ID == 0:
        return True
    return update.effective_user.id == ALLOWED_USER_ID

# ─────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────

def clean_nominal(text: str) -> int:
    """75.000 / 75,000 / 75000 → 75000"""
    return int(re.sub(r"[^\d]", "", text) or "0")

def parse_laporan(text: str) -> dict:
    """
    Parse pesan format:
    LAPORAN KITFIX HARIAN Tanggal: 27/05/2026
    PEMASUKAN
    1. Nama | Jasa | Harga | Metode | Status
    PENGELUARAN
    1. Keterangan | Nominal | Metode
    """
    result = {"tanggal": None, "pemasukan": [], "pengeluaran": [], "errors": []}

    # Tanggal
    tgl_match = re.search(r"tanggal\s*:\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})", text, re.IGNORECASE)
    if tgl_match:
        result["tanggal"] = tgl_match.group(1)
    else:
        result["tanggal"] = datetime.now().strftime("%d/%m/%Y")
        result["errors"].append("⚠️ Tanggal tidak ditemukan, pakai tanggal hari ini.")

    # Split bagian PEMASUKAN dan PENGELUARAN
    pemasukan_block = ""
    pengeluaran_block = ""

    pem_match = re.search(r"PEMASUKAN(.*?)(?=PENGELUARAN|$)", text, re.IGNORECASE | re.DOTALL)
    pen_match = re.search(r"PENGELUARAN(.*?)$", text, re.IGNORECASE | re.DOTALL)

    if pem_match:
        pemasukan_block = pem_match.group(1)
    if pen_match:
        pengeluaran_block = pen_match.group(1)

    # Parse baris pemasukan: nomor. Nama | Jasa | Harga | Metode | Status
    for line in pemasukan_block.splitlines():
        line = line.strip()
        if not line:
            continue
        # Hapus nomor urut di awal (1. / 1) / - dll)
        line = re.sub(r"^\d+[\.\)]\s*", "", line)
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        try:
            row = {
                "Nama Pelanggan": parts[0] if len(parts) > 0 else "",
                "Jasa":           parts[1] if len(parts) > 1 else "",
                "Harga (Rp)":     clean_nominal(parts[2]) if len(parts) > 2 else 0,
                "Metode Bayar":   parts[3] if len(parts) > 3 else "",
                "Status":         parts[4] if len(parts) > 4 else "",
                "Catatan":        parts[5] if len(parts) > 5 else "",
            }
            result["pemasukan"].append(row)
        except Exception as e:
            result["errors"].append(f"⚠️ Gagal parse pemasukan: `{line}` ({e})")

    # Parse baris pengeluaran: nomor. Keterangan | Nominal | Metode
    for line in pengeluaran_block.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^\d+[\.\)]\s*", "", line)
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        try:
            row = {
                "Kategori Pengeluaran": parts[0] if len(parts) > 0 else "",
                "Nominal (Rp)":        clean_nominal(parts[1]) if len(parts) > 1 else 0,
                "Metode Bayar":        parts[2] if len(parts) > 2 else "",
            }
            result["pengeluaran"].append(row)
        except Exception as e:
            result["errors"].append(f"⚠️ Gagal parse pengeluaran: `{line}` ({e})")

    return result

def format_rp(angka: int) -> str:
    return f"Rp {angka:,}".replace(",", ".")

# ─────────────────────────────────────────────────
# HANDLERS
# ─────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text(
        "👋 *Bot Laporan KitFix* siap!\n\n"
        "Kirim laporan harian langsung dengan format:\n\n"
        "```\n"
        "LAPORAN KITFIX HARIAN Tanggal: 27/05/2026\n"
        "PEMASUKAN\n"
        "1. Budi | Reparasi Sepatu | 75.000 | QRIS | Lunas\n"
        "2. Sari | Jahit Tas | 120.000 | Tunai | DP\n"
        "PENGELUARAN\n"
        "1. Beli lem sepatu | 50.000 | Tunai\n"
        "2. Tagihan listrik | 150.000 | Transfer\n"
        "```\n\n"
        "Perintah lain:\n"
        "• /contoh — lihat contoh format lengkap\n"
        "• /help — bantuan",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text(
        "*Format Laporan Harian KitFix:*\n\n"
        "*Header (wajib):*\n"
        "`LAPORAN KITFIX HARIAN Tanggal: DD/MM/YYYY`\n\n"
        "*Pemasukan* (Nama | Jasa | Harga | Metode | Status):\n"
        "• Metode: `Tunai` / `Transfer` / `QRIS`\n"
        "• Status: `Lunas` / `DP` / `Belum Bayar`\n\n"
        "*Pengeluaran* (Keterangan | Nominal | Metode):\n"
        "• Metode: `Tunai` / `Transfer` / `QRIS`\n\n"
        "Harga bisa pakai titik: `75.000` atau tanpa: `75000`\n"
        "Kolom Status dan Catatan di pemasukan boleh dikosongkan.",
        parse_mode="Markdown"
    )

async def contoh_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text(
        "📋 *Contoh laporan harian:*\n\n"
        "```\n"
        "LAPORAN KITFIX HARIAN Tanggal: 27/05/2026\n"
        "PEMASUKAN\n"
        "1. Budi Santoso | Reparasi Sepatu Nike | 75.000 | QRIS | Lunas\n"
        "2. Sari Dewi | Jahit Tas Kulit | 120.000 | Tunai | DP\n"
        "3. Andi | Ganti Sol Sandal | 45.000 | Transfer | Lunas\n"
        "PENGELUARAN\n"
        "1. Beli lem sepatu | 50.000 | Tunai\n"
        "2. Tagihan listrik | 150.000 | Transfer\n"
        "```\n\n"
        "Tinggal copy, edit isinya, kirim — selesai! ✅",
        parse_mode="Markdown"
    )

async def handle_laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    text = update.message.text.strip()

    # Harus ada kata LAPORAN atau PEMASUKAN supaya tidak trigger sembarang pesan
    if not re.search(r"(LAPORAN|PEMASUKAN|PENGELUARAN)", text, re.IGNORECASE):
        await update.message.reply_text(
            "Pesan tidak dikenali sebagai format laporan.\n"
            "Ketik /contoh untuk lihat format yang benar."
        )
        return

    await update.message.reply_text("⏳ Memproses laporan...")

    parsed = parse_laporan(text)
    tanggal = parsed["tanggal"]
    pemasukan_rows = parsed["pemasukan"]
    pengeluaran_rows = parsed["pengeluaran"]
    errors = parsed["errors"]

    if not pemasukan_rows and not pengeluaran_rows:
        await update.message.reply_text(
            "❌ Tidak ada data yang bisa dibaca.\n"
            "Cek format kamu dengan /contoh"
        )
        return

    saved_pem = 0
    saved_pen = 0
    fail_msgs = list(errors)

    # Simpan pemasukan
    for row in pemasukan_rows:
        row["Tanggal"] = tanggal
        try:
            append_pemasukan(row)
            saved_pem += 1
        except Exception as e:
            fail_msgs.append(f"❌ Gagal simpan pemasukan '{row.get('Nama Pelanggan', '')}': {e}")

    # Simpan pengeluaran
    for row in pengeluaran_rows:
        row["Tanggal"] = tanggal
        try:
            append_pengeluaran(row)
            saved_pen += 1
        except Exception as e:
            fail_msgs.append(f"❌ Gagal simpan pengeluaran '{row.get('Kategori Pengeluaran', '')}': {e}")

    # Hitung total
    total_pem = sum(r.get("Harga (Rp)", 0) for r in pemasukan_rows)
    total_pen = sum(r.get("Nominal (Rp)", 0) for r in pengeluaran_rows)

    # Susun reply
    lines = [f"✅ *Laporan {tanggal} berhasil disimpan!*\n"]

    if pemasukan_rows:
        lines.append(f"💰 *Pemasukan ({saved_pem} transaksi):*")
        for r in pemasukan_rows:
            lines.append(f"  • {r['Nama Pelanggan']} — {r['Jasa']} — {format_rp(r['Harga (Rp)'])} ({r.get('Status', '-')})")
        lines.append(f"  *Total: {format_rp(total_pem)}*\n")

    if pengeluaran_rows:
        lines.append(f"🧾 *Pengeluaran ({saved_pen} item):*")
        for r in pengeluaran_rows:
            lines.append(f"  • {r['Kategori Pengeluaran']} — {format_rp(r['Nominal (Rp)'])}")
        lines.append(f"  *Total: {format_rp(total_pen)}*\n")

    lines.append(f"📊 *Profit hari ini: {format_rp(total_pem - total_pen)}*")

    if fail_msgs:
        lines.append("\n" + "\n".join(fail_msgs))

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ─────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("contoh", contoh_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_laporan))
    logger.info("Bot KitFix berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
