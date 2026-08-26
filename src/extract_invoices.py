"""
AI-Powered Invoice & Receipt Data Extraction Tool
--------------------------------------------------
OCR + rule-based field extraction pipeline that reads invoice images and
produces a clean, Tally/Excel-import-ready spreadsheet.

Pipeline:
    image -> Tesseract OCR -> raw text -> regex field extraction -> pandas DataFrame -> Excel

Note on the "LLM extraction" upgrade path:
    This offline build uses regex/rule-based extraction so it runs with zero
    external API calls. The extract_fields() function is written so you can
    swap in an LLM call (OpenAI/Gemini/Claude) that takes `raw_text` and
    returns the same field dictionary, if you want fuzzier extraction for
    invoices that don't follow a fixed layout.
"""
import os
import re
import glob
import numpy as np
import cv2
import pandas as pd
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample_invoices")
OUTPUT_XLSX = os.path.join(os.path.dirname(__file__), "..", "output", "extracted_invoices.xlsx")


def preprocess(path: str) -> Image.Image:
    """Grayscale + Otsu threshold — only applied when image is not already high-contrast."""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    mean = img.mean()
    # Skip thresholding for already clean/white-background images
    if mean > 200:
        return Image.fromarray(img)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(img)


def ocr_image(path: str) -> str:
    img = preprocess(path)
    return pytesseract.image_to_string(img, config="--psm 6")


def extract_fields(raw_text: str, source_file: str) -> dict:
    def find(pattern, text, group=1, cast=str, default=None):
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            return default
        try:
            return cast(m.group(group))
        except Exception:
            return default

    vendor_match = raw_text.strip().split("\n")[0].strip() if raw_text.strip() else None

    # OCR garbles "No" as "Na/Nar" and currency symbol "Rs" as "Ps/Fs/Bs"
    _num = r"[\d,]+\.\d{2}"
    _cur = r"[A-Za-z]{1,2}\.?\s*"

    invoice_no = find(r"Invoice\s*N[a-z]*[:.\s]+([A-Z0-9][A-Z0-9\.\-]{3,})", raw_text)
    inv_date = find(r"Invoice\s*Date[:.\s]+([\d][\d\-/]+)", raw_text)
    # GSTIN: 15-char alphanumeric, may have a single OCR space mid-value
    gstin = find(r"GSTIN\s*([A-Z0-9]{5,15}(?:\s[A-Z0-9]{1,10})?)", raw_text,
                 cast=lambda s: re.sub(r"\s+", "", s)[:15])
    subtotal = find(r"Subto[a-z]{0,3}[:.\s]+" + _cur + r"(" + _num + r")", raw_text,
                    cast=lambda s: float(s.replace(",", "")))
    gst_rate = find(r"GST\s*[\(]?(\d+)%", raw_text, cast=int)
    gst_amount = find(r"GST\s*[\(]?\d+%[\)%]?[:.\s]+" + _cur + r"(" + _num + r")", raw_text,
                      cast=lambda s: float(s.replace(",", "")))
    total = find(r"Total\s*Amount[:.\s]+" + _cur + r"(" + _num + r")", raw_text,
                 cast=lambda s: float(s.replace(",", "")))

    key_fields = [invoice_no, inv_date, gstin, total]
    confidence = round(sum(v is not None for v in key_fields) / len(key_fields) * 100)

    return {
        "source_file": os.path.basename(source_file),
        "vendor": vendor_match,
        "invoice_no": invoice_no,
        "invoice_date": inv_date,
        "gstin": gstin,
        "subtotal": subtotal,
        "gst_rate_pct": gst_rate,
        "gst_amount": gst_amount,
        "total_amount": total,
        "confidence_pct": confidence,
        "needs_review": any(v is None for v in key_fields),
    }


def run(data_dir: str = DATA_DIR, output_xlsx: str = OUTPUT_XLSX) -> pd.DataFrame:
    images = sorted(glob.glob(os.path.join(data_dir, "*.png")))
    if not images:
        raise FileNotFoundError(
            f"No invoice images found in {data_dir}. "
            "Run generate_sample_invoices.py first, or point this at your own scans."
        )

    rows = []
    for path in images:
        text = ocr_image(path)
        rows.append(extract_fields(text, path))

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_xlsx), exist_ok=True)

    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Extracted Invoices", index=False)
        summary = pd.DataFrame({
            "metric": ["Invoices processed", "Flagged for review", "Total GST amount", "Total invoice value"],
            "value": [
                len(df),
                int(df["needs_review"].sum()),
                round(df["gst_amount"].infer_objects(copy=False).fillna(0).sum(), 2),
                round(df["total_amount"].infer_objects(copy=False).fillna(0).sum(), 2),
            ],
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)

    return df


if __name__ == "__main__":
    df = run()
    print(df.to_string(index=False))
    print(f"\nSaved extraction report to {OUTPUT_XLSX}")
