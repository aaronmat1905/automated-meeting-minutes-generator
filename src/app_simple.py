"""
Simplified Flask Application - NO GOOGLE CLOUD REQUIRED!
Only needs Gemini API key for AI features
"""

import logging
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json

from src.config_simple import get_config
from src.services.audio_processor import AudioProcessor, AudioProcessingError
from src.services.assemblyai_transcription import AssemblyAITranscriptionService, TranscriptionError
from src.services.gemini_agent import GeminiAgent, GeminiAgentError
from src.services.document_generator import DocumentGenerator, DocumentGenerationError

# Initialize Flask app
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Load configuration
config = get_config()
app.config.from_object(config)
config.init_app(app)

# Enable CORS
CORS(app)

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize basic services (no API keys needed)
audio_processor = AudioProcessor(config)
document_generator = DocumentGenerator(config)

# Lazy-load services that need API keys
transcription_service = None
gemini_service = None

def get_transcription_service():
    """Lazy load transcription service"""
    global transcription_service
    if transcription_service is None:
        if not config.ASSEMBLYAI_API_KEY:
            raise TranscriptionError(
                "AssemblyAI API key not configured. "
                "Please add ASSEMBLYAI_API_KEY to your .env file. "
                "Get a FREE key at: https://www.assemblyai.com/dashboard/signup"
            )
        logger.info("Initializing AssemblyAI transcription service...")
        transcription_service = AssemblyAITranscriptionService(config)
    return transcription_service

def get_gemini_service():
    """Lazy load Gemini service"""
    global gemini_service
    if gemini_service is None:
        if not config.GEMINI_API_KEY:
            raise GeminiAgentError(
                "Gemini API key not configured. "
                "Please add GEMINI_API_KEY to your .env file. "
                "Get a FREE key at: https://makersuite.google.com/app/apikey"
            )
        logger.info("Initializing Gemini AI service...")
        gemini_service = GeminiAgent(config)
    return gemini_service


# ========== WEB UI ROUTES ==========

@app.route('/')
def index():
    """Main web interface"""
    return render_template('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(config.STATIC_FOLDER, filename)


# ========== API ROUTES ==========

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Meeting Minutes Generator (Simplified)',
        'version': '2.0.0',
        'gemini_configured': config.GEMINI_API_KEY is not None,
        'assemblyai_configured': config.ASSEMBLYAI_API_KEY is not None
    }), 200


@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """Upload audio file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get meeting metadata
        meeting_metadata = {}
        if 'metadata' in request.form:
            try:
                meeting_metadata = json.loads(request.form['metadata'])
            except json.JSONDecodeError:
                pass

        # Save file
        filename = secure_filename(file.filename)
        file_path = audio_processor.save_uploaded_file(file, filename)

        # Validate
        audio_metadata = audio_processor.validate_audio_file(file_path)
        audio_metadata['meeting_metadata'] = meeting_metadata

        logger.info(f"Audio uploaded: {filename}")

        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': Path(file_path).stem,
            'file_path': file_path,
            'metadata': audio_metadata
        }), 200

    except AudioProcessingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio file"""
    try:
        data = request.get_json()

        if not data or 'file_path' not in data:
            return jsonify({'error': 'file_path is required'}), 400

        file_path = data['file_path']
        language = data.get('language', config.TRANSCRIPTION_LANGUAGE)
        metadata = data.get('metadata', {})

        # Transcribe (AssemblyAI handles all formats)
        logger.info(f"Transcribing {file_path}...")
        transcriber = get_transcription_service()
        result = transcriber.transcribe_audio(file_path, language=language, metadata=metadata)

        return jsonify({
            'message': 'Transcription completed',
            'full_transcript': result['full_transcript'],
            'segments': result['segments'],
            'transcript_file': result['transcript_file'],
            'metadata': result['metadata']
        }), 200

    except TranscriptionError as e:
        logger.error(f"Transcription error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_transcript():
    """Analyze transcript with Gemini"""
    try:
        data = request.get_json()

        if not data or 'transcript' not in data:
            return jsonify({'error': 'transcript is required'}), 400

        transcript = data['transcript']

        # Load from file if path provided
        if isinstance(transcript, str) and os.path.exists(transcript):
            with open(transcript, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
                transcript = transcript_data.get('full_transcript', transcript)

        metadata = data.get('metadata', {})

        # Analyze
        logger.info("Analyzing transcript...")
        gemini = get_gemini_service()
        analysis = gemini.analyze_transcript(transcript, metadata)

        return jsonify({
            'message': 'Analysis completed',
            'analysis': analysis
        }), 200

    except GeminiAgentError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-minutes', methods=['POST'])
def generate_minutes():
    """Generate meeting minutes"""
    try:
        data = request.get_json()

        if not data or 'meeting_data' not in data or 'analysis' not in data:
            return jsonify({'error': 'meeting_data and analysis required'}), 400

        meeting_data = data['meeting_data']
        analysis = data['analysis']
        template = data.get('template', 'MRS')
        formats = data.get('formats', ['pdf', 'markdown'])

        logger.info(f"Generating minutes ({template})...")
        output_files = document_generator.generate_minutes(
            meeting_data,
            analysis,
            template=template,
            formats=formats
        )

        return jsonify({
            'message': 'Minutes generated',
            'files': output_files,
            'template': template
        }), 200

    except DocumentGenerationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/process-meeting', methods=['POST'])
def process_meeting():
    """Complete pipeline: upload -> transcribe -> analyze -> generate"""
    try:
        # Upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get parameters
        meeting_metadata = {}
        if 'metadata' in request.form:
            meeting_metadata = json.loads(request.form['metadata'])

        template = request.form.get('template', 'MRS')
        formats = request.form.get('formats', 'pdf,markdown').split(',')
        language = request.form.get('language', config.TRANSCRIPTION_LANGUAGE)

        # Save and validate
        filename = secure_filename(file.filename)
        file_path = audio_processor.save_uploaded_file(file, filename)
        audio_metadata = audio_processor.validate_audio_file(file_path)

        logger.info(f"Processing meeting: {filename}")

        # Transcribe
        logger.info("Step 1/3: Transcribing with AssemblyAI...")
        transcriber = get_transcription_service()
        transcript_result = transcriber.transcribe_audio(file_path, language=language, metadata=meeting_metadata)

        # Analyze
        logger.info("Step 2/3: Analyzing with Gemini...")
        gemini = get_gemini_service()
        analysis = gemini.analyze_transcript(
            transcript_result['full_transcript'],
            meeting_metadata
        )

        # Generate minutes
        logger.info("Step 3/3: Generating minutes...")
        meeting_data = {
            **meeting_metadata,
            'duration': f"{audio_metadata.get('duration_minutes', 0):.1f} minutes",
        }

        minutes_files = document_generator.generate_minutes(
            meeting_data,
            analysis,
            template=template,
            formats=formats
        )

        return jsonify({
            'message': 'Meeting processed successfully!',
            'transcript_file': transcript_result['transcript_file'],
            'transcript': transcript_result['full_transcript'],
            'segments': transcript_result['segments'],
            'analysis': analysis,
            'minutes_files': minutes_files
        }), 200

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Download generated files"""
    try:
        # Check export folder
        file_path = config.EXPORT_FOLDER / filename
        if not file_path.exists():
            file_path = config.TRANSCRIPT_FOLDER / filename

        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        return send_file(str(file_path), as_attachment=True, download_name=filename)

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'File not found'}), 404


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    logger.info("=" * 60)
    logger.info("Meeting Minutes Generator - Simplified Version")
    logger.info("=" * 60)
    logger.info(f"Starting on http://localhost:{port}")
    logger.info(f"AssemblyAI Configured: {config.ASSEMBLYAI_API_KEY is not None}")
    logger.info(f"Gemini Configured: {config.GEMINI_API_KEY is not None}")
    logger.info("=" * 60)

    app.run(
        host='0.0.0.0',
        port=port,
        debug=config.DEBUG
    )
