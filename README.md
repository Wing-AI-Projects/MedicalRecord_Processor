# Medical Record Extractor

A Flask-based web application that extracts structured medical data from PDF health records using Claude AI, with automatic PII/PHI redaction for privacy protection.

## Features

- **PDF Text Extraction**: Extract text from medical record PDFs using PyMuPDF
- **Privacy Protection**: Automatic redaction of sensitive patient information (PII/PHI)
- **AI-Powered Extraction**: Uses Claude AI to extract structured medical data
- **Patient Demographics**: Sex, Age, Race, Height, Weight
- **Medical Data**: Diagnoses, Medications, Lab Results, Vital Signs, Allergies
- **Web Interface**: Clean, responsive UI for uploading and viewing results
- **Debug Mode**: Save pipeline outputs for troubleshooting (local development)
- **Serverless Ready**: Designed for Vercel deployment with in-memory processing

## Architecture

### Data Flow Pipeline

```
PDF Upload → Text Extraction → PII/PHI Redaction → Claude AI Analysis → Schema Transform → Frontend Display
```

### Components

1. **pdf_processor.py** - PDF text extraction and PII/PHI redaction
2. **medical_data_extractor.py** - Claude AI integration for structured data extraction
3. **schema_transformer.py** - Transform Claude output to frontend format
4. **app.py** - Flask web server with REST API
5. **templates/index.html** - Frontend UI
6. **static/js/script.js** - Client-side JavaScript

### Debug System

When `DEBUG_MODE=true`, the application saves outputs at each pipeline stage:
- `debug/{timestamp}_{id}_1_raw_extracted.txt` - Raw PDF text
- `debug/{timestamp}_{id}_2_redacted.txt` - Redacted text
- `debug/{timestamp}_{id}_3_claude_output.json` - Claude's extracted data
- `debug/{timestamp}_{id}_4_final_response.json` - Transformed frontend data

## Installation

### Prerequisites

- Python 3.8+
- Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MedicalRecordExtractor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```bash
   # Anthropic API Configuration
   ANTHROPIC_API_KEY=your-api-key-here

   # Claude Model Selection
   CLAUDE_MODEL=claude-sonnet-4-5

   # Debug Mode (set to 'true' to enable debug file outputs)
   DEBUG_MODE=false
   ```

## Usage

### Local Development

1. **Start the Flask server**
   ```bash
   python app.py
   ```

2. **Open your browser**

   Navigate to `http://localhost:5001`

3. **Upload a PDF**

   - Drag and drop or click to browse for a medical record PDF
   - Maximum file size: 50MB
   - Supported format: PDF only

4. **View results**

   The extracted data will be displayed in tabs:
   - Overview: Patient demographics and quick stats
   - Diagnoses: Medical conditions with ICD codes
   - Medications: Prescriptions with dosage and frequency
   - Lab Results: Test results with status indicators
   - Vital Signs: Blood pressure, heart rate, etc.
   - Allergies: Known allergens and reactions
   - Notes: Clinical findings and assessments

### Debug Mode

Enable debug mode to troubleshoot extraction issues:

1. Set `DEBUG_MODE=true` in your `.env` file
2. Restart the Flask app
3. Upload a PDF
4. Check the `debug/` folder for pipeline outputs

### API Endpoints

- `GET /` - Web interface
- `POST /api/upload` - Upload PDF for processing
- `GET /api/health` - Health check endpoint

## Deployment

### Quick Deploy to Vercel

For detailed deployment instructions, see **[DEPLOYMENT.md](DEPLOYMENT.md)** - comprehensive guide with multiple deployment methods.

#### Quick Start (3 steps)

1. **Run the deployment script**
   ```bash
   ./deploy.sh
   ```

2. **Or deploy manually with Vercel CLI**
   ```bash
   npx vercel login
   npx vercel --prod
   ```

3. **Or use Vercel Dashboard**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Add environment variables (see below)
   - Click Deploy

#### Required Environment Variables

Add these in your Vercel project settings:
- `ANTHROPIC_API_KEY` - Your Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))
- `CLAUDE_MODEL` - Model name (default: `claude-sonnet-4-5`)

**For complete deployment guide with troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md)**

Note: Debug mode is disabled in production (Vercel has ephemeral filesystem)

## Privacy & Security

### Defensive Security Features

- **Automatic PII/PHI Redaction**: Removes names, phone numbers, SSNs, emails, addresses, MRNs, DOBs
- **Privacy-First Design**: Redaction occurs BEFORE sending data to Claude AI
- **Multiple Redaction Layers**: Specific patient names + generic patterns
- **No Persistent Storage**: All processing is in-memory (serverless compatible)
- **Gitignored Outputs**: Debug files and medical records never committed to git

### Redacted Information Types

- Patient names
- Phone numbers
- Social Security Numbers (SSNs)
- Email addresses
- Medical Record Numbers (MRNs)
- Physical addresses
- ZIP codes
- Dates of birth
- Account numbers
- Credit card numbers
- Driver's license numbers

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | - | Yes |
| `CLAUDE_MODEL` | Claude model to use | `claude-sonnet-4-5` | No |
| `DEBUG_MODE` | Enable debug file outputs | `false` | No |

### Supported Claude Models

- `claude-sonnet-4-5` (Recommended)
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`

## Development

### Project Structure

```
MedicalRecordExtractor/
├── app.py                      # Flask web server
├── pdf_processor.py            # PDF extraction & redaction
├── medical_data_extractor.py   # Claude AI integration
├── schema_transformer.py       # Data transformation
├── templates/
│   └── index.html             # Frontend HTML
├── static/
│   ├── css/style.css          # Styles
│   └── js/script.js           # Client-side logic
├── debug/                     # Debug outputs (gitignored)
├── uploads/                   # Temporary uploads (gitignored)
├── requirements.txt           # Python dependencies
├── vercel.json               # Vercel configuration
├── .env                      # Environment variables (gitignored)
├── .gitignore                # Git ignore rules
├── .vercelignore             # Vercel ignore rules
└── README.md                 # This file
```

### Adding New Data Fields

To extract additional data from medical records:

1. **Update Claude prompt** in `medical_data_extractor.py`:
   - Add new fields to the JSON schema in the extraction prompt

2. **Update schema transformer** in `schema_transformer.py`:
   - Add transformation function for new data type
   - Update `transform_claude_output_to_frontend()`

3. **Update frontend** in `templates/index.html` and `static/js/script.js`:
   - Add HTML elements for new fields
   - Add JavaScript to populate and display data

4. **Test with debug mode** enabled to verify extraction

## Troubleshooting

### Common Issues

**Issue**: "Claude API returned empty content"
- **Solution**: Check your `ANTHROPIC_API_KEY` in `.env` file
- **Solution**: Verify the API key is valid at [Anthropic Console](https://console.anthropic.com/)

**Issue**: "Failed to parse JSON response"
- **Solution**: Enable `DEBUG_MODE=true` and check `debug/*_3_claude_output.json`
- **Solution**: The issue may be with Claude's response format (check logs)

**Issue**: Debug files not being created
- **Solution**: Ensure `DEBUG_MODE=true` in `.env` file
- **Solution**: Restart the Flask app after changing `.env`
- **Solution**: Check that `load_dotenv()` is called in `app.py`

**Issue**: "No module named 'dotenv'"
- **Solution**: Install dependencies: `pip install -r requirements.txt`

### Kill Running Flask Process

```bash
# Find the process
ps aux | grep "python.*app.py" | grep -v grep

# Kill it
pkill -f "python.*app.py"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is intended for educational and authorized healthcare use only. Ensure compliance with HIPAA and other healthcare privacy regulations in your jurisdiction.

## Acknowledgments

- **Anthropic Claude AI** - For powerful medical data extraction
- **PyMuPDF (fitz)** - For PDF text extraction
- **Flask** - For the web framework
- **Vercel** - For serverless deployment platform

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**⚠️ Important**: This tool is designed for defensive security and privacy protection. Always verify extracted medical data accuracy and comply with healthcare privacy regulations (HIPAA, GDPR, etc.) in your region.
