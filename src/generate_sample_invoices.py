"""
Generates a handful of realistic-looking sample invoice images (PNG) so the
extraction pipeline has something to run on. In a real deployment, you'd point
extract_invoices.py at your own scanned invoices/receipts instead.
"""
import os
import random
from datetime import date, timedelta
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample_invoices")
os.makedirs(OUT_DIR, exist_ok=True)

VENDORS = ["Bluewave Traders", "Kanpur Office Supplies", "Sharma Electricals",
           "Nova Print Solutions", "Ganga Logistics Pvt Ltd"]

def font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()

def make_invoice(idx: int):
    vendor = random.choice(VENDORS)
    invoice_no = f"INV-{2000 + idx}"
    inv_date = (date(2026, 1, 1) + timedelta(days=random.randint(0, 240))).strftime("%d-%m-%Y")
    subtotal = round(random.uniform(1500, 45000), 2)
    gst_rate = random.choice([5, 12, 18])
    gst_amount = round(subtotal * gst_rate / 100, 2)
    total = round(subtotal + gst_amount, 2)
    gstin = f"09AAAPL{1000+idx}A1Z{idx % 9}"

    img = Image.new("RGB", (900, 500), "white")
    d = ImageDraw.Draw(img)
    f_title = font(28)
    f_body = font(20)

    d.text((40, 30), vendor, font=f_title, fill="black")
    d.text((40, 70), "TAX INVOICE", font=f_body, fill="black")
    d.line([(40, 105), (860, 105)], fill="black", width=2)

    d.text((40, 130), f"Invoice No: {invoice_no}", font=f_body, fill="black")
    d.text((40, 165), f"Invoice Date: {inv_date}", font=f_body, fill="black")
    d.text((40, 200), f"GSTIN: {gstin}", font=f_body, fill="black")

    d.text((40, 260), f"Subtotal: Rs. {subtotal:,.2f}", font=f_body, fill="black")
    d.text((40, 295), f"GST ({gst_rate}%): Rs. {gst_amount:,.2f}", font=f_body, fill="black")
    d.text((40, 330), f"Total Amount: Rs. {total:,.2f}", font=f_title, fill="black")

    d.text((40, 420), "Thank you for your business.", font=f_body, fill="black")

    path = os.path.join(OUT_DIR, f"invoice_{idx:03d}.png")
    img.save(path)
    return path

if __name__ == "__main__":
    random.seed(42)
    paths = [make_invoice(i) for i in range(1, 9)]
    print(f"Generated {len(paths)} sample invoices in {OUT_DIR}")
