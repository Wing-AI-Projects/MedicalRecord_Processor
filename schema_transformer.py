"""
Schema Transformer

Transforms Claude API medical data extraction output into the format
expected by the frontend web application.

This bridges the gap between the AI extraction schema and the UI display schema.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


def determine_lab_status(value: str, reference_range: Optional[str], abnormal_flag: Optional[str]) -> str:
    """
    Determine the status of a lab result (Normal/High/Low/Critical).

    Args:
        value: The lab value as a string
        reference_range: Reference range like "70-100" or "<5.7"
        abnormal_flag: Optional flag from the lab report

    Returns:
        str: Status label (Normal, High, Low, or Critical)
    """
    # If abnormal flag is provided, use it
    if abnormal_flag:
        flag_lower = abnormal_flag.lower()
        if 'high' in flag_lower or 'elevated' in flag_lower:
            return 'High'
        elif 'low' in flag_lower:
            return 'Low'
        elif 'critical' in flag_lower:
            return 'Critical'
        elif 'normal' in flag_lower:
            return 'Normal'

    # Try to parse numeric value and compare to range
    if reference_range and value:
        try:
            # Extract numeric value
            numeric_value = float(''.join(c for c in value if c.isdigit() or c == '.'))

            # Parse reference range
            if '-' in reference_range:
                # Range format: "70-100"
                parts = reference_range.split('-')
                low = float(''.join(c for c in parts[0] if c.isdigit() or c == '.'))
                high = float(''.join(c for c in parts[1] if c.isdigit() or c == '.'))

                if numeric_value < low:
                    return 'Low'
                elif numeric_value > high:
                    return 'High'
                else:
                    return 'Normal'
            elif '<' in reference_range:
                # Less than format: "<5.7"
                threshold = float(''.join(c for c in reference_range if c.isdigit() or c == '.'))
                if numeric_value >= threshold:
                    return 'High'
                else:
                    return 'Normal'
            elif '>' in reference_range:
                # Greater than format: ">60"
                threshold = float(''.join(c for c in reference_range if c.isdigit() or c == '.'))
                if numeric_value <= threshold:
                    return 'Low'
                else:
                    return 'Normal'
        except (ValueError, IndexError):
            pass

    # Default to Normal if we can't determine
    return 'Normal'


def transform_diagnoses(claude_diagnoses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform diagnoses from Claude format to frontend format.

    Claude format: {"condition": "...", "icd_code": "...", "date": "..."}
    Frontend format: {"code": "...", "description": "...", "date": "..."}
    """
    transformed = []
    for diagnosis in claude_diagnoses:
        transformed.append({
            "code": diagnosis.get("icd_code", ""),
            "description": diagnosis.get("condition", ""),
            "date": diagnosis.get("date", "")
        })
    return transformed


def transform_medications(claude_medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform medications from Claude format to frontend format.

    Claude format: {"name": "...", "dosage": "...", "frequency": "...", "route": "..."}
    Frontend format: {"name": "...", "dosage": "...", "frequency": "...", "indication": "..."}
    """
    transformed = []
    for medication in claude_medications:
        transformed.append({
            "name": medication.get("name", ""),
            "dosage": medication.get("dosage", ""),
            "frequency": medication.get("frequency", ""),
            "indication": medication.get("route", "")  # Map route to indication for now
        })
    return transformed


def transform_lab_results(claude_lab_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform lab results from Claude format to frontend format.

    Claude format: {"test_name": "...", "value": "...", "units": "...", "reference_range": "...", "abnormal_flag": "..."}
    Frontend format: {"test_name": "...", "value": "...", "unit": "...", "reference_range": "...", "status": "...", "date": "..."}
    """
    transformed = []
    for lab in claude_lab_results:
        value = lab.get("value", "")
        reference_range = lab.get("reference_range", "")
        abnormal_flag = lab.get("abnormal_flag", "")

        transformed.append({
            "test_name": lab.get("test_name", ""),
            "value": value,
            "unit": lab.get("units", ""),
            "reference_range": reference_range,
            "date": lab.get("date", ""),
            "status": determine_lab_status(value, reference_range, abnormal_flag)
        })
    return transformed


def transform_vital_signs(claude_vital_signs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform vital signs from Claude format to frontend format.

    Claude format: {"measurement_type": "...", "value": "...", "units": "...", "date": "..."}
    Frontend format: {"parameter": "...", "value": "...", "unit": "...", "date": "..."}
    """
    transformed = []
    for vital in claude_vital_signs:
        # Convert measurement_type to friendly parameter name
        measurement_type = vital.get("measurement_type", "")
        parameter_mapping = {
            "blood_pressure": "Blood Pressure",
            "heart_rate": "Heart Rate",
            "temperature": "Temperature",
            "respiratory_rate": "Respiratory Rate",
            "o2_saturation": "O2 Saturation",
            "weight_bmi": "Weight/BMI"
        }
        parameter = parameter_mapping.get(measurement_type, measurement_type.replace('_', ' ').title())

        transformed.append({
            "parameter": parameter,
            "value": vital.get("value", ""),
            "unit": vital.get("units", ""),
            "date": vital.get("date", "")
        })
    return transformed


def transform_clinical_findings_to_notes(claude_clinical_findings: List[Dict[str, Any]]) -> str:
    """
    Transform clinical findings array into a single clinical notes string.

    Claude format: [{"category": "...", "finding": "...", "date": "..."}]
    Frontend format: Single string with all findings
    """
    if not claude_clinical_findings:
        return ""

    notes_parts = []
    for finding in claude_clinical_findings:
        category = finding.get("category", "").replace('_', ' ').title()
        finding_text = finding.get("finding", "")
        date = finding.get("date", "")

        if date:
            notes_parts.append(f"[{date}] {category}: {finding_text}")
        else:
            notes_parts.append(f"{category}: {finding_text}")

    return " | ".join(notes_parts)


def create_patient_info() -> Dict[str, str]:
    """
    Create patient info section with redacted placeholders.

    Since all PII is redacted, we return placeholder values.
    The frontend UI will display these appropriately.
    """
    return {
        "name": "[REDACTED]",
        "dob": "[REDACTED]",
        "mrn": "[REDACTED]",
        "date_of_visit": datetime.now().strftime("%Y-%m-%d")
    }


def transform_claude_output_to_frontend(claude_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main transformation function that converts Claude API output to frontend format.

    Args:
        claude_data: Dictionary containing Claude's structured extraction

    Returns:
        Dictionary in the format expected by the frontend
    """
    # Transform each section
    transformed_data = {
        "patient_info": create_patient_info(),
        "diagnoses": transform_diagnoses(claude_data.get("diagnoses", [])),
        "medications": transform_medications(claude_data.get("medications", [])),
        "lab_results": transform_lab_results(claude_data.get("lab_results", [])),
        "vital_signs": transform_vital_signs(claude_data.get("vital_signs", [])),
        "allergies": claude_data.get("allergies", []),  # Already in correct format
        "clinical_notes": transform_clinical_findings_to_notes(claude_data.get("clinical_findings", []))
    }

    # Wrap in success response
    return {
        "status": "success",
        "data": transformed_data
    }


def transform_error_to_frontend(error_message: str, error_type: str = "extraction_error") -> Dict[str, Any]:
    """
    Transform an error into the frontend error format.

    Args:
        error_message: The error message to display
        error_type: Type of error (extraction_error, validation_error, api_error, etc.)

    Returns:
        Dictionary with error response
    """
    return {
        "status": "error",
        "error_type": error_type,
        "message": error_message
    }
