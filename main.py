#!/usr/bin/env python3
"""
Medical Record PDF Text Extractor
Simple tool to extract text from medical record PDFs using pdfplumber
"""

import sys
import os
import re
import argparse
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


def extract_text_from_pdf(pdf_path):
    """
    Extract plain text from a PDF file using pdfplumber.
    Simple text extraction without table detection for better reliability.

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        str: Extracted text from all pages
    """
    try:
        # Open the PDF file
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""

            # Iterate through all pages
            for page_num, page in enumerate(pdf.pages):
                full_text += f"\n{'='*60}\n"
                full_text += f"Page {page_num + 1}\n"
                full_text += f"{'='*60}\n"

                # Extract plain text only
                text = page.extract_text()
                full_text += text

        return full_text

    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def redact_sensitive_information(text):
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
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',  # (123) 456-7890
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',    # 123-456-7890 or 123.456.7890
        r'\b\d{10}\b',                       # 1234567890
        r'\+?1?\s*\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'  # +1 (123) 456-7890
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


def save_text_to_markdown(text, output_path, redact=True):
    """
    Save extracted text to a markdown file with optional PII/PHI redaction.

    Args:
        text (str): The text to save
        output_path (str): Path to the output markdown file
        redact (bool): Whether to redact sensitive information (default: True)

    Returns:
        str: The path to the saved file
    """
    try:
        # Redact sensitive information if requested
        text_to_save = redact_sensitive_information(text) if redact else text

        # Add a header noting redaction status
        header = "# Medical Record Extract\n\n"
        if redact:
            header += "**Note:** Sensitive information has been redacted for privacy protection.\n\n"
            header += "---\n\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header + text_to_save)
        return output_path
    except Exception as e:
        raise Exception(f"Error saving to markdown file: {str(e)}")


def main():
    """Main function to handle command-line execution."""

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Extract text from medical record PDFs with privacy protection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py medical_record.pdf
  python main.py medical_record.pdf --output ./output
  python main.py medical_record.pdf --extract-data
  python main.py medical_record.pdf --output ./output --extract-data
        """
    )

    parser.add_argument('pdf_path',
                        help='Path to the PDF file to extract')
    parser.add_argument('-o', '--output',
                        dest='output_folder',
                        help='Directory to save the output markdown file (default: same as PDF)')
    parser.add_argument('--extract-data',
                        action='store_true',
                        help='Extract structured medical data using Claude API after PDF extraction')

    args = parser.parse_args()

    pdf_path = args.pdf_path
    output_folder = args.output_folder

    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found - {pdf_path}")
        sys.exit(1)

    # Check if file is a PDF
    if not pdf_path.lower().endswith('.pdf'):
        print(f"Error: File must be a PDF - {pdf_path}")
        sys.exit(1)

    # If output folder is specified, validate and create if needed
    if output_folder:
        # Convert to absolute path
        output_folder = os.path.abspath(output_folder)

        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
                print(f"Created output directory: {output_folder}")
            except Exception as e:
                print(f"Error: Cannot create output directory - {str(e)}")
                sys.exit(1)
        elif not os.path.isdir(output_folder):
            print(f"Error: Output path exists but is not a directory - {output_folder}")
            sys.exit(1)

    try:
        print(f"Extracting text from: {pdf_path}\n")

        # Extract text (no console output)
        extracted_text = extract_text_from_pdf(pdf_path)

        # Generate output filename
        pdf_filename = os.path.basename(pdf_path)
        base_name = os.path.splitext(pdf_filename)[0]
        output_filename = f"{base_name}_extracted.md"

        # Determine output path
        if output_folder:
            output_path = os.path.join(output_folder, output_filename)
        else:
            # Save in same directory as PDF
            pdf_dir = os.path.dirname(pdf_path) or '.'
            output_path = os.path.join(pdf_dir, output_filename)

        # Save to markdown file with redaction
        saved_path = save_text_to_markdown(extracted_text, output_path, redact=True)

        print(f"\n{'='*60}")
        print("Extraction completed successfully!")
        print(f"Text saved to: {saved_path}")
        print("\nNote: Sensitive information (names, addresses, phone numbers, etc.)")
        print("has been redacted from the saved file for privacy protection.")

        # Extract structured medical data if requested
        if args.extract_data:
            print(f"\n{'='*60}")
            print("Starting medical data extraction with Claude API...")
            print(f"{'='*60}\n")

            try:
                from medical_data_extractor import extract_medical_data
                analysis_path = extract_medical_data(saved_path)
                print(f"\n{'='*60}")
                print("Medical data extraction completed!")
                print(f"Analysis saved to: {analysis_path}")
                print(f"{'='*60}")
            except ImportError:
                print("\n✗ Error: medical_data_extractor module not found.")
                print("Please ensure medical_data_extractor.py is in the same directory.")
                sys.exit(1)
            except Exception as e:
                print(f"\n✗ Medical data extraction failed: {str(e)}")
                print("The redacted markdown file was saved successfully, but Claude analysis failed.")
                sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()