# AI-Powered Invoice & Receipt Data Extraction Tool

Reads invoice/receipt images, OCRs them, extracts key fields (vendor, invoice
number, date, GSTIN, subtotal, GST amount, total), and produces a clean Excel
report that's ready to hand off to accounting or import into Tally.

## Why this project
Connects hands-on bookkeeping/Tally experience with an automated document
pipeline — the kind of tool that saves real hours of manual data entry.

## Pipeline
```
invoice image --> Tesseract OCR --> raw text --> regex field extraction --> pandas --> Excel report
```

## Tech stack
- Python, Pillow (sample invoice generation)
- Tesseract OCR (via pytesseract)
- pandas + openpyxl (Excel report)

## How to run
```bash
cd src
python3 generate_sample_invoices.py   # creates 8 sample invoice images in data/sample_invoices/
python3 extract_invoices.py            # OCRs them and writes output/extracted_invoices.xlsx
```

## Output
`output/extracted_invoices.xlsx` with two sheets:
- **Extracted Invoices** — one row per invoice with all extracted fields, plus a
  `needs_review` flag for any invoice where a key field couldn't be parsed
- **Summary** — totals across all processed invoices

## Using your own invoices
Drop your own scanned invoices/receipts (PNG/JPG) into `data/sample_invoices/`
(or point `run()` at a different folder) and re-run `extract_invoices.py`.
For invoices that don't follow a fixed layout, swap the regex-based
`extract_fields()` for an LLM call (GPT/Gemini/Claude) that takes the OCR'd
text and returns the same field dictionary — the rest of the pipeline (Excel
export, review flagging) stays the same.

## Suggested resume bullet
"Built an OCR + rule-based invoice extraction pipeline that parses vendor,
GSTIN, and tax fields from scanned invoices into an audit-ready Excel report,
flagging ambiguous fields for manual review."
