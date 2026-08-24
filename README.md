# Tools-for-csv-template-matching

A Streamlit app that takes a raw CSV export and turns it into a clean, template-ready file — map messy column names to the fields you actually need, filter out rows you don't want, and export a platform-specific format (e.g. Facebook Custom Audiences).

## What it does

1. **Upload a CSV** — handles encoding issues automatically (falls back from UTF-8 to Latin-1) and skips malformed lines instead of crashing on them.
2. **Map columns** — pick which of your CSV's columns correspond to standard fields (`full name`, `email`, `company`, `city`, `state`, `country`, `phone`, `linkedin url`, `company website`) via dropdowns. No need to rename columns by hand.
3. **Clean rows** — apply operator-based row filters (column *is empty*, *equals*, *contains*, *greater than*, etc.) to delete or keep matching rows. Operations stack, so you can chain multiple cleanup steps.
4. **Export to a template** — generate a platform-ready CSV (currently: Facebook Custom Audience format — `fn`, `ln`, `phone`, `ct`, `st`, `country`) and download it directly from the browser.

## Why

Audience lists and contact exports rarely come in the exact shape a target platform wants. This tool removes the manual spreadsheet work of renaming columns, dropping incomplete rows, and reformatting for upload — all through a simple point-and-click interface, no code required to run it.

## Requirements

- Python 3.9+
- [pandas](https://pandas.pydata.org/)
- [streamlit](https://streamlit.io/)

Install dependencies:

```bash
pip install pandas streamlit
```

## Running the app

```bash
streamlit run main.py
```

This opens the app in your browser at `http://localhost:8501`. Upload a CSV, map your columns, apply any row filters, and download the result.

## Project structure

```
.
├── main.py               # Streamlit entrypoint
├── column_cleaning.py     # Core logic: file reading, column mapping UI, row filtering, template export
└── README.md
```

## Roadmap / ideas

- [ ] Additional export templates (Google Ads Customer Match, Mailchimp, etc.)
- [ ] Undo for individual row operations (currently: full reset only)
- [ ] Duplicate-column detection when multiple source columns map to the same target field
