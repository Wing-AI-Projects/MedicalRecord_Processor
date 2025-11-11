"""
Medical Data Extractor using Claude API

This module processes redacted medical record markdown files and extracts
structured medical information using Anthropic's Claude API.

Output format: JSON with structured data including:
- Diagnoses (conditions, ICD codes)
- Medications (name, dosage, frequency, route)
- Lab Results (test name, value, units, reference range, date)
- Key Dates (visits, procedures, onsets, follow-ups)
- Procedures
- Vital Signs (blood pressure, heart rate, temperature, etc.)
- Clinical Findings (symptoms, physical exam, assessments, recommendations)
"""

import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError

# Load environment variables
load_dotenv()


class MedicalDataExtractionError(Exception):
    """Custom exception for medical data extraction errors."""
    pass


def extract_medical_data_from_text(redacted_text: str, model: Optional[str] = None) -> dict:
    """
    Extract structured medical data from redacted text content using Claude API.

    This is the in-memory version designed for serverless environments.
    Returns parsed JSON dict instead of saving to file.

    Args:
        redacted_text: The redacted medical record text content
        model: Optional Claude model to use. If None, uses CLAUDE_MODEL from .env
               Options: 'claude-sonnet-4-5', 'claude-3-5-sonnet-20241022', or 'claude-3-5-haiku-20241022'

    Returns:
        dict: Parsed JSON with structured medical data

    Raises:
        MedicalDataExtractionError: If extraction fails or JSON parsing fails
    """

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

    # Normalize model names (Vercel might use different format)
    model_mapping = {
        "claude-sonnet-4-5": "claude-sonnet-4-20250514",
        "sonnet": "claude-sonnet-4-20250514",
        "haiku": "claude-3-5-haiku-20241022"
    }
    model = model_mapping.get(model, model)

    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

    # Construct the extraction prompt
    extraction_prompt = f"""You are a medical information extraction specialist. Analyze the following redacted medical record and extract key medical information into a structured JSON format.

IMPORTANT: This medical record has already been redacted to protect patient privacy. Do not attempt to infer or reconstruct any redacted information marked as [REDACTED].

Please extract and organize the information according to the following JSON schema. Return ONLY valid JSON with no additional text or markdown formatting:

{{
  "patient_demographics": {{
    "sex": "string (optional) - e.g., Male, Female, Other, Unknown",
    "age": "string (optional) - age or age range if mentioned",
    "race": "string (optional) - race/ethnicity if mentioned",
    "height": "string (optional) - with units e.g., '5\\'10\\\"', '178 cm'",
    "weight": "string (optional) - with units e.g., '165 lbs', '75 kg'"
  }},
  "diagnoses": [
    {{
      "condition": "string",
      "icd_code": "string (optional)",
      "date": "string (optional)"
    }}
  ],
  "medications": [
    {{
      "name": "string",
      "dosage": "string",
      "frequency": "string",
      "route": "string (optional)"
    }}
  ],
  "lab_results": [
    {{
      "test_name": "string",
      "value": "string",
      "units": "string",
      "reference_range": "string (optional)",
      "date": "string (optional)",
      "abnormal_flag": "string (optional)"
    }}
  ],
  "key_dates": [
    {{
      "date": "string",
      "event_type": "string (visit/procedure/symptom_onset/follow_up)",
      "description": "string"
    }}
  ],
  "procedures": [
    {{
      "name": "string",
      "date": "string (optional)",
      "description": "string (optional)"
    }}
  ],
  "vital_signs": [
    {{
      "measurement_type": "string (blood_pressure/heart_rate/temperature/respiratory_rate/o2_saturation/weight_bmi)",
      "value": "string",
      "units": "string (optional)",
      "date": "string (optional)"
    }}
  ],
  "clinical_findings": [
    {{
      "category": "string (symptom/physical_exam/assessment/recommendation/other)",
      "finding": "string",
      "date": "string (optional)"
    }}
  ],
  "allergies": [
    {{
      "allergen": "string",
      "reaction": "string (optional)"
    }}
  ]
}}

For each array, if no information is found, return an empty array []. Do not include explanatory text - return only the JSON object.

Here is the redacted medical record to analyze:

---
{redacted_text}
---

Return the structured JSON extraction:"""

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

        # Check if response has content
        if not message.content or len(message.content) == 0:
            raise MedicalDataExtractionError(
                f"Claude API returned empty content. Response: {message}"
            )

        # Extract the response text
        extracted_data = message.content[0].text

        # Check if extracted data is empty
        if not extracted_data or extracted_data.strip() == "":
            raise MedicalDataExtractionError(
                f"Claude API returned empty text. Full message: {message}"
            )

        # Validate and parse JSON response
        try:
            # Try to parse the JSON to validate it
            parsed_json = json.loads(extracted_data)
        except json.JSONDecodeError as e:
            # If Claude returns JSON wrapped in markdown code blocks, extract it
            if "```" in extracted_data:
                # Strip markdown code blocks
                # Remove opening ```json or ```
                if extracted_data.strip().startswith("```json"):
                    extracted_data = extracted_data.strip()[7:]  # Remove ```json
                elif extracted_data.strip().startswith("```"):
                    extracted_data = extracted_data.strip()[3:]  # Remove ```

                # Remove closing ```
                if extracted_data.strip().endswith("```"):
                    extracted_data = extracted_data.strip()[:-3]  # Remove trailing ```

                # Try parsing again
                try:
                    parsed_json = json.loads(extracted_data.strip())
                except json.JSONDecodeError as e2:
                    raise MedicalDataExtractionError(
                        f"Failed to parse JSON after removing markdown: {e2}\n"
                        f"Response text (first 500 chars): {extracted_data[:500]}"
                    )
            else:
                raise MedicalDataExtractionError(
                    f"Failed to parse JSON response: {e}\n"
                    f"Response text (first 500 chars): {extracted_data[:500]}"
                )

        return parsed_json

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


def extract_medical_data(markdown_path: str, model: Optional[str] = None) -> str:
    """
    Extract structured medical data from a redacted markdown file using Claude API.

    Args:
        markdown_path: Path to the redacted markdown file (_extracted.md)
        model: Optional Claude model to use. If None, uses CLAUDE_MODEL from .env
               Options: 'claude-3-5-sonnet-20241022' or 'claude-3-5-haiku-20241022'

    Returns:
        Path to the generated JSON analysis file (_analysis.json)

    Raises:
        MedicalDataExtractionError: If extraction fails or JSON parsing fails
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

    print(f"Sending to Claude API (model: {model or os.getenv('CLAUDE_MODEL', 'claude-3-5-haiku-20241022')})...")

    # Use the in-memory function
    parsed_json = extract_medical_data_from_text(redacted_content, model)

    # Generate output filename
    output_path = markdown_file.parent / f"{markdown_file.stem.replace('_extracted', '')}_analysis.json"

    # Create metadata wrapper for the JSON output
    output_data = {
        "_metadata": {
            "generated_by": "Claude AI Medical Data Extractor",
            "source_file": str(markdown_file.name),
            "privacy_notice": "This analysis is based on a redacted medical record. All patient identifying information has been removed to protect privacy.",
            "disclaimer": "This is an AI-generated analysis for informational purposes only. It should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers.",
            "model": model
        },
        "extracted_data": parsed_json
    }

    # Save the structured extraction as formatted JSON
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

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
