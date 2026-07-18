# PII Redaction Tool

A Python-based tool that reads a DOCX document (Red Herring Prospectus), detects all Personally Identifiable Information (PII), and replaces each instance with a **consistent fake alternative** using the Faker library.

## Approach

### Hybrid Detection Pipeline

The tool uses a **two-pronged detection strategy**:

1. **Regex Pattern Matching** — Custom regular expressions detect structured PII types:
   - Email addresses (`user@domain.com` patterns)
   - Phone numbers (Indian `+91` format and international)
   - SSNs (`XXX-XX-XXXX`)
   - Credit card numbers (Visa, MasterCard, Amex patterns)
   - IP addresses (`X.X.X.X`)
   - Dates of birth (context-aware: only dates near keywords like "born", "DOB")
   - PAN numbers (Indian `ABCDE1234F` format)
   - CIN numbers (Corporate Identity Numbers)
   - SEBI registration numbers
   - Website URLs

2. **Keyword/Entity Matching** — A curated list of known entity names extracted from document analysis:
   - Person names (directors, officers, promoters, contact persons)
   - Company/organization names
   - Physical/mailing addresses (registered offices, corporate offices)

### Why Not Pure NER?

While spaCy NER models work well for general text, Red Herring Prospectus documents contain:
- **Indian names** that standard English NER models often miss
- **Company names** that overlap with common words (e.g., "The Federal Bank Limited")
- **Addresses** interleaved with table formatting

A keyword-based approach for these entity types provides **near-perfect recall** on known document content, while regex handles structured patterns with high precision.

### Consistent Replacement Strategy

- Each unique PII instance is mapped to a **single fake replacement** that persists across the entire document
- The same name always maps to the same fake name (e.g., `Kushal Subbayya Hegde` → `John Robert Smith` everywhere)
- The `Faker` library generates realistic replacements (names → names, emails → emails, etc.)
- A fixed random seed ensures **reproducible** outputs

## PII Types Detected

| PII Type | Count | Method |
|---|---|---|
| Person Names | 37 unique | Keyword matching |
| Email Addresses | 25 unique | Regex |
| Phone Numbers | 18 unique | Regex (Indian format) |
| Company Names | 21 unique | Keyword matching |
| Physical Addresses | 30+ unique | Keyword matching |
| Websites | 14 unique | Regex |
| CIN Numbers | 4 unique | Regex |
| SEBI Reg. Numbers | 6 unique | Regex |
| SSNs | Detected if present | Regex |
| Credit Card Numbers | Detected if present | Regex |
| IP Addresses | Detected if present | Regex |
| Dates of Birth | Context-aware | Regex |

## How to Run

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run Redaction
```bash
python redact.py --input input.docx --output output_redacted.docx
```

### Run Evaluation
```bash
python evaluate.py
```

## Files

| File | Purpose |
|---|---|
| `redact.py` | Main script — orchestrates detection, replacement, and output |
| `pii_detector.py` | PII detection engine (regex + keyword matching) |
| `pii_replacer.py` | Consistent fake replacement generator (Faker) |
| `docx_handler.py` | DOCX read/write with formatting preservation |
| `evaluate.py` | Evaluation script (precision, recall, F1) |
| `config.py` | Configuration, patterns, and false positive filters |
| `requirements.txt` | Python dependencies |

## Tradeoffs & Known Limitations

### False Positives
- **Website URLs**: Some URLs for non-PII sites (e.g., SEBI, BSE) are intentionally excluded via a government domain filter, but edge cases may slip through
- **Phone numbers**: The regex may match some non-phone digit sequences embedded in financial data; we mitigate this by requiring ≥10 digits

### False Negatives
- **Newly mentioned names**: If a person is mentioned only once deep in the text and not in our curated list, they may be missed. Mitigation: We extracted names from a thorough manual review
- **Non-standard address formats**: Some addresses without clear PIN codes or city names may be partially detected

### Design Decisions
- **Regulatory entities not redacted**: Bodies like SEBI, BSE, NSE, RBI are intentionally left unredacted as they are public regulatory bodies, not PII
- **Indian state names not redacted**: Maharashtra, Gujarat, etc. are geographic identifiers, not personally identifiable
- **CIN and SEBI registration numbers ARE redacted**: These uniquely identify specific companies and are considered PII in this context

## Evaluation Results

| Metric | Value |
|---|---|
| **Accuracy** | **81.82%** |
| **Precision** | **83.24%** |
| **Recall** | **97.96%** |
| **F1 Score** | **90.00%** |

A manual leak scan of the output document confirms **zero original PII terms remain**.

See [`evaluation_report.md`](evaluation_report.md) for detailed per-category breakdown, methodology, and limitations.
