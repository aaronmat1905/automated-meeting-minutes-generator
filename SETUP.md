# Setup Guide - Meeting Minutes Generator

Complete setup guide for the AI-Based Smart Meeting Minutes Generator using Google Cloud and Gemini.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Google Cloud Setup](#google-cloud-setup)
3. [Gemini API Setup](#gemini-api-setup)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Python 3.9 or higher
- pip (Python package manager)
- Git
- Google Cloud account
- Gemini API key

### Optional (for integrations)
- Jira account (for Jira integration)
- Asana account (for Asana integration)
- Redis (for async task processing)

---

## Google Cloud Setup

### 1. Create Google Cloud Project

```bash
# Install Google Cloud SDK (if not already installed)
# Windows: Download from https://cloud.google.com/sdk/docs/install
# Linux/Mac:
curl https://sdk.cloud.google.com | bash

# Initialize gcloud
gcloud init

# Create new project
gcloud projects create your-project-id --name="Meeting Minutes Generator"

# Set as active project
gcloud config set project your-project-id
```

### 2. Enable Required APIs

```bash
# Enable Speech-to-Text API
gcloud services enable speech.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage-api.googleapis.com

# Enable Calendar API
gcloud services enable calendar-json.googleapis.com
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create meeting-minutes-sa \
    --display-name="Meeting Minutes Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:meeting-minutes-sa@your-project-id.iam.gserviceaccount.com" \
    --role="roles/speech.admin"

gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:meeting-minutes-sa@your-project-id.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create and download service account key
gcloud iam service-accounts keys create credentials.json \
    --iam-account=meeting-minutes-sa@your-project-id.iam.gserviceaccount.com

# Store the credentials.json file securely
```

### 4. Create Cloud Storage Bucket

```bash
# Create bucket for audio files
gsutil mb -p your-project-id -c STANDARD -l us-central1 gs://your-bucket-name

# Set bucket permissions
gsutil iam ch serviceAccount:meeting-minutes-sa@your-project-id.iam.gserviceaccount.com:objectAdmin \
    gs://your-bucket-name
```

---

## Gemini API Setup

### 1. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key (you'll need this for configuration)

### 2. Verify API Access

```python
# Test script to verify Gemini API access
import google.generativeai as genai

genai.configure(api_key='YOUR_API_KEY')
model = genai.GenerativeModel('gemini-1.5-pro')
response = model.generate_content('Hello!')
print(response.text)
```

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/pestechnology/PESU_RR_AIML_A_P34_Automated_Meeting_Minutes_Generator_Ramen-Noodles.git
cd PESU_RR_AIML_A_P34_Automated_Meeting_Minutes_Generator_Ramen-Noodles
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Install additional tools
pip install pytest-cov flake8 black
```

---

## Configuration

### 1. Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Edit .env File

```bash
# Open .env in your text editor and fill in the values:

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Google Cloud Storage
GCS_BUCKET_NAME=your-bucket-name

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=generate-a-random-secret-key

# Optional: Jira Integration
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token

# Optional: Asana Integration
ASANA_ACCESS_TOKEN=your-asana-access-token
ASANA_WORKSPACE_ID=your-workspace-id
```

### 3. Generate Secret Key

```python
# Run this Python command to generate a secret key:
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Create Required Directories

```bash
mkdir -p data/uploads data/transcripts data/exports logs
```

---

## Running the Application

### 1. Development Mode

```bash
# Set Flask environment
export FLASK_APP=src.app
export FLASK_ENV=development

# Run the application
python -m src.app

# Or use Flask CLI
flask run --host=0.0.0.0 --port=5000
```

### 2. Production Mode (using Gunicorn)

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 600 src.app:app

# Or with configuration file
gunicorn --config gunicorn_config.py src.app:app
```

### 3. Access the API

- API Base URL: `http://localhost:5000`
- Health Check: `http://localhost:5000/health`
- API Documentation: `http://localhost:5000/api/docs` (if Swagger configured)

---

## Testing

### 1. Run All Tests

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test files
pytest tests/unit/test_audio_processor.py -v
pytest tests/unit/test_gemini_agent.py -v
pytest tests/integration/test_api_endpoints.py -v
```

### 2. Run Linting

```bash
# Run flake8
flake8 src/ --max-line-length=120

# Format code with black
black src/ tests/
```

### 3. Test Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open coverage report (Windows)
start htmlcov/index.html

# Open coverage report (Linux/Mac)
open htmlcov/index.html
```

---

## Testing the API

### 1. Using cURL

```bash
# Upload audio file
curl -X POST http://localhost:5000/api/upload \
  -F "file=@/path/to/audio.mp3" \
  -F 'metadata={"title":"Team Meeting","participants":["Alice","Bob"]}'

# Transcribe audio
curl -X POST http://localhost:5000/api/transcribe \
  -H "Content-Type: application/json" \
  -d '{"file_path":"/path/to/audio.mp3","enable_diarization":true}'

# Complete processing
curl -X POST http://localhost:5000/api/process-meeting \
  -F "file=@/path/to/audio.mp3" \
  -F 'metadata={"title":"Team Meeting"}' \
  -F "template=MRS" \
  -F "formats=pdf,markdown"
```

### 2. Using Python Requests

```python
import requests

# Upload and process meeting
url = "http://localhost:5000/api/process-meeting"
files = {
    'file': open('meeting_audio.mp3', 'rb'),
    'metadata': (None, '{"title":"Team Meeting","participants":["Alice","Bob"]}'),
    'template': (None, 'MRS'),
    'formats': (None, 'pdf,markdown')
}

response = requests.post(url, files=files)
print(response.json())
```

### 3. Test with Sample Audio

```bash
# Create a test audio file (requires ffmpeg)
ffmpeg -f lavfi -i sine=frequency=1000:duration=10 -ac 2 test_audio.mp3

# Process the test file
curl -X POST http://localhost:5000/api/process-meeting \
  -F "file=@test_audio.mp3" \
  -F 'metadata={"title":"Test Meeting"}' \
  -F "template=MRS"
```

---

## Troubleshooting

### Common Issues

#### 1. Google Cloud Authentication Error

```
Error: Could not authenticate with Google Cloud
```

**Solution:**
- Verify `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Check that credentials.json exists and has proper permissions
- Run: `gcloud auth application-default login`

#### 2. Gemini API Error

```
Error: GEMINI_API_KEY not configured
```

**Solution:**
- Ensure `GEMINI_API_KEY` is set in `.env` file
- Verify API key is active in Google AI Studio
- Check API quota limits

#### 3. Audio File Upload Error

```
Error: Unsupported audio format
```

**Solution:**
- Supported formats: MP3, WAV, MP4, M4A, FLAC, OGG
- Convert file using: `ffmpeg -i input.xxx -acodec libmp3lame output.mp3`

#### 4. Transcription Timeout

```
Error: Transcription timeout
```

**Solution:**
- Increase `TRANSCRIPTION_TIMEOUT_SECONDS` in config
- For large files (>10MB), ensure GCS bucket is configured
- Check Google Cloud quotas

#### 5. Memory Error with Large Files

```
MemoryError: Unable to allocate array
```

**Solution:**
- Split audio into smaller chunks
- Increase system memory
- Use async processing with Celery

### Debug Mode

Enable detailed logging:

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Run application
python -m src.app
```

### Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Google Cloud project created
- [ ] Service account credentials downloaded
- [ ] GCS bucket created
- [ ] Gemini API key obtained
- [ ] `.env` file configured
- [ ] Required directories created
- [ ] Tests passing
- [ ] API health check responds

---

## Next Steps

1. **API Documentation**: Set up Swagger/OpenAPI documentation
2. **Frontend**: Build web interface for easier access
3. **Monitoring**: Set up logging and monitoring (e.g., Cloud Logging)
4. **CI/CD**: Configure automated testing and deployment
5. **Scaling**: Deploy to Google Cloud Run or App Engine

---

## Support

For issues and questions:
- Create an issue on GitHub
- Contact: [Your Team Email]
- Documentation: See `docs/` folder

---

## License

This project is developed for educational purposes as part of PES University coursework.
