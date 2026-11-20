# Evals (M1-M2)

Planned:
- Field-level accuracy (exact match after normalization) for: issuer RFC/tax ID, receiver,
  invoice date, currency, subtotal, taxes, total, line items.
- Approaches compared on the same set: pdfplumber + regex baseline, Textract AnalyzeExpense,
  Claude (two model tiers).
- Cost per invoice and latency per approach.
