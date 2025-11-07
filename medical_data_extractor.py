"""
Medical Data Extractor using Claude API

This module processes redacted medical record markdown files and extracts
structured medical information using Anthropic's Claude API.

Key extracted information:
- Diagnoses (conditions, ICD codes)
- Medications (name, dosage, frequency)
- Lab Results (test name, value, units, reference range, date)
- Key Dates (visits, procedures, onsets)
- Procedures
- Other Clinical Findings (symptoms, vital signs, assessments)
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError

# Load environment variables
load_dotenv()


class MedicalDataExtractionError(Exception):
    """Custom exception for medical data extraction errors."""
    pass


def extract_medical_data(markdown_path: str, model: Optional[str] = None) -> str:
    """
    Extract structured medical data from a redacted markdown file using Claude API.

    Args:
        markdown_path: Path to the redacted markdown file (_extracted.md)
        model: Optional Claude model to use. If None, uses CLAUDE_MODEL from .env
               Options: 'claude-3-5-sonnet-20241022' or 'claude-3-5-haiku-20241022'

    Returns:
        Path to the generated analysis file (_analysis.md)

    Raises:
        MedicalDataExtractionError: If extraction fails
        FileNotFoundError: If markdown file doesn't exist
    """

    # Validate input file
    markdown_file = Path(markdown_path)
    if not markdown_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    # Get API key and model from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        raise MedicalDataExtractionError(
            "ANTHROPIC_API_KEY not set in .env file. "
            "Please add your API key from https://console.anthropic.com/settings/keys"
        )

    # Determine which model to use
    if model is None:
        model = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-20241022")

    print(f"Reading redacted medical record from: {markdown_path}")

    # Read the redacted markdown content
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            redacted_content = f.read()
    except Exception as e:
        raise MedicalDataExtractionError(f"Failed to read markdown file: {e}")

    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

    # Construct the extraction prompt
    extraction_prompt = f"""You are a medical information extraction specialist. Analyze the following redacted medical record and extract key medical information into a structured format.

IMPORTANT: This medical record has already been redacted to protect patient privacy. Do not attempt to infer or reconstruct any redacted information marked as [REDACTED].

Please extract and organize the following information into clearly labeled sections:

## 1. DIAGNOSES
List all diagnoses, conditions, or medical problems mentioned. Include ICD codes if present.

## 2. MEDICATIONS
List all medications with details:
- Medication name
- Dosage
- Frequency/schedule
- Route (if mentioned)

## 3. LAB RESULTS
List all laboratory test results with:
- Test name
- Value
- Units
- Reference range (if provided)
- Date (if mentioned)
- Abnormal flag (if indicated)

## 4. KEY DATES
Extract important dates:
- Visit dates
- Procedure dates
- Symptom onset dates
- Follow-up appointments

## 5. PROCEDURES
List any procedures, surgeries, or interventions mentioned.

## 6. VITAL SIGNS
List vital signs if present:
- Blood pressure
- Heart rate
- Temperature
- Respiratory rate
- O2 saturation
- Weight/BMI

## 7. OTHER CLINICAL FINDINGS
Include:
- Symptoms reported
- Physical examination findings
- Clinical assessments
- Recommendations
- Any other relevant medical information

For each section, if no information is found, write "None documented" rather than leaving the section empty.

Here is the redacted medical record to analyze:

---
{redacted_content}
---

Provide your structured extraction below:"""

    print(f"Sending to Claude API (model: {model})...")

    # Call Claude API
    try:
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": extraction_prompt
                }
            ]
        )

        # Extract the response text
        extracted_data = message.content[0].text

    except RateLimitError as e:
        raise MedicalDataExtractionError(
            f"Rate limit exceeded. Please try again later. Error: {e}"
        )
    except APIConnectionError as e:
        raise MedicalDataExtractionError(
            f"Network connection error. Please check your internet connection. Error: {e}"
        )
    except APIError as e:
        raise MedicalDataExtractionError(
            f"Claude API error: {e}"
        )
    except Exception as e:
        raise MedicalDataExtractionError(
            f"Unexpected error during Claude API call: {e}"
        )

    # Generate output filename
    output_path = markdown_file.parent / f"{markdown_file.stem.replace('_extracted', '')}_analysis.md"

    # Create header for the analysis file
    analysis_header = """# Medical Record Analysis
# Generated by Claude AI

**IMPORTANT PRIVACY NOTICE:**
This analysis is based on a redacted medical record. All patient identifying
information has been removed to protect privacy.

**Disclaimer:** This is an AI-generated analysis for informational purposes only.
It should not be used as a substitute for professional medical advice, diagnosis,
or treatment. Always consult with qualified healthcare providers.

---

"""

    # Save the structured extraction
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(analysis_header)
            f.write(extracted_data)

        print(f"✓ Medical data extraction completed successfully!")
        print(f"✓ Analysis saved to: {output_path}")

        return str(output_path)

    except Exception as e:
        raise MedicalDataExtractionError(f"Failed to save analysis file: {e}")


def main():
    """
    CLI entry point for standalone usage.

    Usage:
        python medical_data_extractor.py <path-to-extracted-markdown>
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python medical_data_extractor.py <path-to-extracted-markdown>")
        print("\nExample:")
        print("  python medical_data_extractor.py Health_Summary_2Pages_extracted.md")
        sys.exit(1)

    markdown_path = sys.argv[1]

    try:
        output_path = extract_medical_data(markdown_path)
        print(f"\n✓ Success! Analysis saved to: {output_path}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
