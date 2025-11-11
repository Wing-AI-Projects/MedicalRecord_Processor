#!/usr/bin/env python3
"""
Medical Record Processor Web Application
Flask-based web server for processing and displaying medical records from PDFs
"""

import os
import json
import io
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime

# Import our processing modules
import pdf_processor
from medical_data_extractor import extract_medical_data_from_text, MedicalDataExtractionError
from schema_transformer import transform_claude_output_to_frontend, transform_error_to_frontend

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# REAL IMPLEMENTATION FUNCTIONS - Integrated from pdf_processor and medical_data_extractor
# ============================================================================

def extract_medical_data_from_pdf(pdf_file_bytes):
    """
    Extract structured medical data from PDF file bytes.

    This function orchestrates the complete pipeline:
    1. Extract text from PDF
    2. Redact PII/PHI for privacy
    3. Send to Claude API for structured extraction
    4. Transform output to frontend format

    Args:
        pdf_file_bytes (bytes): PDF file content as bytes

    Returns:
        dict: Structured medical data in frontend format

    Raises:
        Exception: If any step of the pipeline fails
    """
    try:
        # Step 1: Extract text from PDF
        raw_text = pdf_processor.extract_text_from_pdf(pdf_file_bytes)

        # Step 2: Redact sensitive information for privacy
        redacted_text = pdf_processor.redact_sensitive_information(raw_text)

        # Step 3: Extract structured data using Claude API
        claude_output = extract_medical_data_from_text(redacted_text)

        # Step 4: Transform to frontend format
        frontend_data = transform_claude_output_to_frontend(claude_output)

        return frontend_data

    except MedicalDataExtractionError as e:
        # Claude API specific errors
        return transform_error_to_frontend(str(e), "api_error")
    except Exception as e:
        # General processing errors
        return transform_error_to_frontend(f"Failed to process PDF: {str(e)}", "processing_error")


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """
    Handle PDF file upload and extract medical data.

    Serverless-compatible: Processes files in-memory without filesystem writes.

    Returns:
        JSON: Extracted medical data or error message
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400

        file = request.files['file']

        # Check if file has a filename
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400

        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': 'Only PDF files are allowed'
            }), 400

        # Read file content into memory
        file_bytes = file.read()

        # Check file size
        if len(file_bytes) > MAX_FILE_SIZE:
            return jsonify({
                'status': 'error',
                'message': 'File is too large (max 50MB)'
            }), 400

        # Validate PDF format (check magic number)
        if not pdf_processor.validate_pdf_format(file_bytes):
            return jsonify({
                'status': 'error',
                'message': 'Invalid PDF file format'
            }), 400

        # Extract medical data (all in-memory, no file writes)
        medical_data = extract_medical_data_from_pdf(file_bytes)

        # medical_data is already in the correct format from transform_claude_output_to_frontend
        # or transform_error_to_frontend, so we can return it directly
        return jsonify(medical_data), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'status': 'error',
        'message': 'File is too large (max 50MB)'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """Handle not found error."""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server error."""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
