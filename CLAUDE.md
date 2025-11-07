# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based medical record PDF text extractor that uses PyMuPDF to extract text from medical record PDFs and automatically redacts sensitive patient information (PII/PHI) for privacy protection.

## Core Architecture

- **Single module design**: All functionality is contained in `main.py`
- **Defensive security focus**: Comprehensive PII/PHI redaction system with multiple regex patterns for various data types
- **CLI-based tool**: Designed for command-line usage with PDF file input

## Dependencies

- PyMuPDF (fitz) >= 1.24.5 for PDF text extraction
- Standard library modules: sys, os, re

## Usage Commands

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the extractor
```bash
python main.py <path-to-pdf-file>
```

Example:
```bash
python main.py Health_Summary_2Pages.pdf
```

### Output
- Extracted text is printed to console
- Redacted text is saved as `<filename>_extracted.md`

## Key Functions

### `extract_text_from_pdf(pdf_path)`
- Uses PyMuPDF to extract text from all pages
- Adds page separators for multi-page documents

### `redact_sensitive_information(text)`
- **Critical security function** - handles PII/PHI redaction
- Redacts: names, phone numbers, SSNs, emails, MRNs, addresses, ZIP codes, DOBs, account numbers, credit cards, driver's licenses
- Uses specific patient name patterns (currently configured for "Wing L Ho", "Wing Ho", "Wing")
- Order matters: specific patient names are redacted FIRST before generic patterns

### `save_text_to_markdown(text, output_path, redact=True)`
- Saves extracted text to markdown with privacy header
- Redaction is enabled by default for safety

## Privacy and Security

This tool is designed for **defensive security** purposes only:
- Automatically redacts sensitive patient information
- Multiple layers of PII/PHI protection
- Privacy-first approach with redaction enabled by default
- Comprehensive regex patterns for various data formats

## Development Notes

- No test framework currently implemented
- No build process - direct Python execution
- Single-file architecture for simplicity
- Error handling throughout with descriptive messages