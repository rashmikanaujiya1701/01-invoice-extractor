import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import pandas as pd
import pytesseract
import streamlit as st
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from extract_invoices import ocr_image, extract_fields


def main():
    st.set_page_config(page_title="Invoice Extractor", page_icon="🧾", layout="wide")
    st.title("🧾 AI-Powered Invoice Extractor")
    st.caption("Upload invoice/receipt images → extract fields → download Excel report")

    uploaded_files = st.file_uploader(
        "Upload invoice images (PNG / JPG)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("Upload one or more invoice images to get started.")
        return

    if not st.button("Extract", type="primary"):
        return

    rows = []
    with st.spinner("Running OCR and extracting fields..."):
        for uf in uploaded_files:
            img = Image.open(uf)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                img.save(tmp.name)
                raw_text = ocr_image(tmp.name)
                row = extract_fields(raw_text, uf.name)
            os.unlink(tmp.name)
            rows.append((uf.name, img, row))

    st.success(f"Processed {len(rows)} invoice(s)")

    df = pd.DataFrame([r for _, _, r in rows])

    # ── Summary metrics ──────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Invoices", len(df))
    m2.metric("Flagged for Review", int(df["needs_review"].sum()))
    m3.metric("Avg Confidence", f"{df['confidence_pct'].mean():.0f}%")
    m4.metric("Total GST", f"₹{df['gst_amount'].fillna(0).sum():,.2f}")
    m5.metric("Total Value", f"₹{df['total_amount'].fillna(0).sum():,.2f}")

    st.divider()

    # ── Per-invoice cards ────────────────────────────────────────────────
    st.subheader("Extracted Fields")
    for fname, img, row in rows:
        with st.expander(f"{'⚠️' if row['needs_review'] else '✅'}  {fname}", expanded=False):
            c1, c2 = st.columns([1, 2])
            c1.image(img, use_container_width=True)
            c2.table(
                pd.DataFrame({
                    "Field": list(row.keys()),
                    "Value": [str(v) if v is not None else "—" for v in row.values()],
                }).set_index("Field")
            )

    st.divider()

    # ── Full results table ───────────────────────────────────────────────
    st.subheader("Results Table")

    def highlight_review(r):
        return ["background-color: #fff3cd" if r["needs_review"] else "" for _ in r]

    st.dataframe(df.style.apply(highlight_review, axis=1), use_container_width=True)

    # ── Excel download ───────────────────────────────────────────────────
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Extracted Invoices", index=False)
        pd.DataFrame({
            "metric": ["Invoices processed", "Flagged for review", "Avg confidence %", "Total GST amount", "Total invoice value"],
            "value": [
                len(df),
                int(df["needs_review"].sum()),
                round(df["confidence_pct"].mean(), 1),
                round(df["gst_amount"].fillna(0).sum(), 2),
                round(df["total_amount"].fillna(0).sum(), 2),
            ],
        }).to_excel(writer, sheet_name="Summary", index=False)

    st.download_button(
        "⬇️ Download Excel Report",
        data=buf.getvalue(),
        file_name="extracted_invoices.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    main()
