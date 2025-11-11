"""
PDF Processing Module

Extracted from main.py for modular use in serverless environments.
Handles PDF text extraction and PII/PHI redaction for privacy protection.

This module is designed to work with both file paths and file-like objects,
making it compatible with serverless architectures like Vercel.
"""

import re
import io
from typing import Union
import pdfplumber


def format_table_as_markdown(table):
    """
    Format a table (list of lists) as a markdown table.
    Removes empty columns and detects single-column tables.

    Args:
        table (list): List of lists representing table rows

    Returns:
        tuple: (formatted_table_str, is_valid_table_bool)
               Returns ("", False) if table quality is too poor
    """
    if not table or len(table) == 0:
        return "", False

    # Filter out empty rows
    table = [row for row in table if any(cell and str(cell).strip() for cell in row)]
    if not table or len(table) == 0:
        return "", False

    # Normalize row lengths
    max_cols = max(len(row) for row in table)
    for row in table:
        while len(row) < max_cols:
            row.append(None)

    # Identify non-empty columns (columns with at least one non-empty cell)
    non_empty_cols = []
    for col_idx in range(max_cols):
        has_content = False
        for row in table:
            if col_idx < len(row) and row[col_idx] and str(row[col_idx]).strip():
                has_content = True
                break
        if has_content:
            non_empty_cols.append(col_idx)

    # If only one non-empty column, treat as plain text instead of table
    if len(non_empty_cols) <= 1:
        # Convert to plain text format
        text_output = "\n"
        for row in table:
            for col_idx in non_empty_cols:
                if col_idx < len(row) and row[col_idx]:
                    text_output += str(row[col_idx]) + "\n"
        return text_output, False

    # Filter columns to only non-empty ones
    filtered_table = []
    for row in table:
        filtered_row = [row[col_idx] if col_idx < len(row) else None
                       for col_idx in non_empty_cols]
        filtered_table.append(filtered_row)

    # Calculate column widths for remaining columns
    col_widths = [0] * len(non_empty_cols)
    for row in filtered_table:
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell else ""
            col_widths[i] = max(col_widths[i], len(cell_str))

    # Build markdown table
    md_table = "\n"
    for row_idx, row in enumerate(filtered_table):
        # Create row
        cells = []
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell else ""
            cells.append(f" {cell_str.ljust(col_widths[i])} ")
        md_table += "|" + "|".join(cells) + "|\n"

        # Add separator after first row (header)
        if row_idx == 0:
            separators = ["-" * (col_widths[i] + 2) for i in range(len(row))]
            md_table += "|" + "|".join(separators) + "|\n"

    return md_table, True


def extract_text_from_pdf(pdf_source: Union[str, bytes, io.BytesIO]) -> str:
    """
    Extract plain text from a PDF file using pdfplumber.
    Supports both file paths and file-like objects for serverless compatibility.

    Args:
        pdf_source: Either:
            - str: Path to the PDF file
            - bytes: PDF file content as bytes
            - io.BytesIO: File-like object containing PDF data

    Returns:
        str: Extracted text from all pages

    Raises:
        Exception: If PDF extraction fails
    """
    try:
        # Handle different input types
        if isinstance(pdf_source, str):
            # File path provided
            pdf_context = pdfplumber.open(pdf_source)
        elif isinstance(pdf_source, bytes):
            # Bytes provided - wrap in BytesIO
            pdf_context = pdfplumber.open(io.BytesIO(pdf_source))
        elif isinstance(pdf_source, io.BytesIO):
            # BytesIO object provided
            pdf_context = pdfplumber.open(pdf_source)
        else:
            raise ValueError(f"Unsupported pdf_source type: {type(pdf_source)}")

        # Extract text from all pages
        with pdf_context as pdf:
            full_text = ""

            # Iterate through all pages
            for page_num, page in enumerate(pdf.pages):
                full_text += f"\n{'='*60}\n"
                full_text += f"Page {page_num + 1}\n"
                full_text += f"{'='*60}\n"

                # Extract plain text only
                text = page.extract_text()
                full_text += text if text else ""

        return full_text

    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def redact_sensitive_information(text: str) -> str:
    """
    Redact personally identifiable information (PII) and protected health information (PHI)
    from the extracted text to protect patient privacy.

    This function removes:
    - Patient names (specific patterns and generic patterns)
    - Phone numbers (various formats)
    - Social Security Numbers
    - Email addresses
    - Medical Record Numbers
    - Account numbers
    - Credit card numbers
    - Dates of birth (including natural language formats)
    - Full addresses
    - ZIP codes
    - Driver's licenses

    Args:
        text (str): The text to redact

    Returns:
        str: Text with sensitive information replaced with [REDACTED] tags
    """
    redacted_text = text

    # IMPORTANT: Redact specific patient names FIRST before other patterns
    # This prevents partial matches and ensures complete name redaction
    # Pattern catches: "Wing L Ho", "Wing L. Ho", "Wing Ho", "Wing" (standalone)
    patient_name_patterns = [
        r'\bWing\s+L\.?\s+Ho\b',  # Wing L Ho or Wing L. Ho
        r'\bWing\s+Ho\b',          # Wing Ho
        r'(?<!")\bWing\b(?!")'     # Wing (but not in quotes like "Wing" nickname)
    ]
    for pattern in patient_name_patterns:
        redacted_text = re.sub(pattern, '[REDACTED-NAME]', redacted_text, flags=re.IGNORECASE)

    # Phone numbers - various formats
    # Matches: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
    phone_patterns = [
        r'\(\d{3}\)\s*\d{3}[-.\\s]?\d{4}',  # (123) 456-7890
        r'\d{3}[-.\\s]\d{3}[-.\\s]\d{4}',    # 123-456-7890 or 123.456.7890
        r'\b\d{10}\b',                       # 1234567890
        r'\+?1?\s*\(\d{3}\)\s*\d{3}[-.\\s]?\d{4}'  # +1 (123) 456-7890
    ]
    for pattern in phone_patterns:
        redacted_text = re.sub(pattern, '[REDACTED-PHONE]', redacted_text)

    # Social Security Numbers (XXX-XX-XXXX)
    redacted_text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED-SSN]', redacted_text)

    # Email addresses
    redacted_text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[REDACTED-EMAIL]',
        redacted_text
    )

    # Medical Record Numbers (MRN, MR#, Medical Record #, etc.)
    mrn_patterns = [
        r'(?i)MRN\s*[:#]?\s*\d+',
        r'(?i)Medical\s+Record\s+(?:Number|#)\s*[:#]?\s*\d+',
        r'(?i)MR\s*#\s*\d+',
        r'(?i)Patient\s+ID\s*[:#]?\s*\d+'
    ]
    for pattern in mrn_patterns:
        redacted_text = re.sub(pattern, '[REDACTED-MRN]', redacted_text)

    # Credit card numbers (basic pattern)
    redacted_text = re.sub(
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        '[REDACTED-CC]',
        redacted_text
    )

    # Account numbers following "Account" or "Acct"
    redacted_text = re.sub(
        r'(?i)(?:Account|Acct)(?:\s+(?:Number|#|No\.?))?\s*[:#]?\s*\d+',
        '[REDACTED-ACCOUNT]',
        redacted_text
    )

    # Dates of birth (various formats including natural language)
    dob_patterns = [
        # Standard formats: DOB: 01/15/1980
        r'(?i)(?:DOB|Date\s+of\s+Birth)\s*[:#]?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
        # Natural language with label: DOB: January 15, 1980
        r'(?i)(?:DOB|Date\s+of\s+Birth)\s*[:#]?\s*\w+\s+\d{1,2},?\s+\d{4}',
        # Natural language with "born": born Mar. 09, 1980 or born March 9, 1980
        r'(?i)\bborn\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}',
        # Full month name with born: born January 15, 1980
        r'(?i)\bborn\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
    ]
    for pattern in dob_patterns:
        redacted_text = re.sub(pattern, '[REDACTED-DOB]', redacted_text)

    # Street addresses (basic pattern - number + street name)
    # Use word boundaries to prevent matching parts of words like "drink"
    redacted_text = re.sub(
        r'\d+\s+[A-Z][a-z]+\s+(?:Street|St\b|Avenue|Ave\b|Road|Rd\b|Boulevard|Blvd\b|Lane|Ln\b|Drive|Dr\b|Court|Ct\b|Way\b|Place|Pl\b)\.?\s*(?:#\d+)?',
        '[REDACTED-ADDRESS]',
        redacted_text,
        flags=re.IGNORECASE
    )

    # ZIP codes (5 digits or 5+4 format)
    # Use negative lookbehind to prevent matching numbers in medical contexts like COVID-19
    redacted_text = re.sub(
        r'(?<!COVID-)(?<!-)\b\d{5}(?:-\d{4})?\b',
        '[REDACTED-ZIP]',
        redacted_text
    )

    # Names following common patterns in medical records
    name_patterns = [
        r'(?i)(?:Patient\s+Name|Name)\s*[:#]?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+',
        r'(?i)(?:First\s+Name)\s*[:#]?\s*[A-Z][a-z]+',
        r'(?i)(?:Last\s+Name)\s*[:#]?\s*[A-Z][a-z]+'
    ]
    for pattern in name_patterns:
        redacted_text = re.sub(pattern, '[REDACTED-NAME]', redacted_text)

    # Driver's License
    redacted_text = re.sub(
        r'(?i)(?:Driver\'?s?\s+License|DL)\s*[:#]?\s*[A-Z0-9]+',
        '[REDACTED-DL]',
        redacted_text
    )

    return redacted_text


def validate_pdf_format(pdf_source: Union[str, bytes, io.BytesIO]) -> bool:
    """
    Validate that the file is a proper PDF by checking the magic number.
    PDF files should start with '%PDF' in the header.

    Args:
        pdf_source: Either:
            - str: Path to the PDF file
            - bytes: PDF file content as bytes
            - io.BytesIO: File-like object containing PDF data

    Returns:
        bool: True if valid PDF format, False otherwise
    """
    try:
        # Get the first few bytes to check magic number
        if isinstance(pdf_source, str):
            # File path - read first bytes
            with open(pdf_source, 'rb') as f:
                header = f.read(5)
        elif isinstance(pdf_source, bytes):
            # Bytes provided
            header = pdf_source[:5]
        elif isinstance(pdf_source, io.BytesIO):
            # BytesIO - save position, read, then restore
            pos = pdf_source.tell()
            pdf_source.seek(0)
            header = pdf_source.read(5)
            pdf_source.seek(pos)
        else:
            return False

        # Check for PDF magic number: %PDF
        return header.startswith(b'%PDF')

    except Exception:
        return False
