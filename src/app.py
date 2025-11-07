"""
Flask Application - Meeting Minutes Generator
Main REST API with endpoints for audio upload, transcription, and minutes generation
"""

import logging
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json

from src.config import get_config
from src.services.audio_processor import AudioProcessor, AudioProcessingError
from src.services.transcription_service import TranscriptionService, TranscriptionError
from src.services.gemini_agent import GeminiAgent, GeminiAgentError
from src.services.document_generator import DocumentGenerator, DocumentGenerationError

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config_name = os.getenv('FLASK_ENV', 'development')
config = get_config(config_name)
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

# Initialize services
audio_processor = AudioProcessor(config)
transcription_service = TranscriptionService(config)
gemini_agent = GeminiAgent(config)
document_generator = DocumentGenerator(config)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Meeting Minutes Generator',
        'version': '1.0.0'
    }), 200


@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """
    Upload audio file for processing

    Request:
        - file: Audio file (multipart/form-data)
        - metadata: JSON string with meeting metadata (optional)

    Response:
        - file_id: Unique identifier for the uploaded file
        - metadata: Audio file metadata
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get meeting metadata if provided
        meeting_metadata = {}
        if 'metadata' in request.form:
            try:
                meeting_metadata = json.loads(request.form['metadata'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid metadata JSON'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = audio_processor.save_uploaded_file(file, filename)

        # Validate audio file
        audio_metadata = audio_processor.validate_audio_file(file_path)

        # Combine metadata
        audio_metadata['meeting_metadata'] = meeting_metadata

        logger.info(f"Audio file uploaded successfully: {filename}")

        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': Path(file_path).stem,
            'file_path': file_path,
            'metadata': audio_metadata
        }), 200

    except AudioProcessingError as e:
        logger.error(f"Audio processing error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in upload: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio file with speaker diarization

    Request JSON:
        - file_path: Path to audio file
        - enable_diarization: Enable speaker diarization (default: true)
        - language_code: Language code (default: en-US)
        - metadata: Meeting metadata (optional)

    Response:
        - transcript: Full transcript text
        - segments: Speaker-segmented transcript
        - speakers: Speaker information
        - transcript_file: Path to saved transcript JSON
    """
    try:
        data = request.get_json()

        if not data or 'file_path' not in data:
            return jsonify({'error': 'file_path is required'}), 400

        file_path = data['file_path']
        enable_diarization = data.get('enable_diarization', True)
        language_code = data.get('language_code', None)
        metadata = data.get('metadata', {})

        # Convert to WAV if needed
        if not file_path.lower().endswith('.wav'):
            logger.info("Converting audio to WAV format...")
            file_path = audio_processor.convert_to_wav(file_path)

        # Transcribe audio
        logger.info(f"Starting transcription for {file_path}...")
        result = transcription_service.transcribe_audio(
            file_path,
            enable_diarization=enable_diarization,
            language_code=language_code,
            metadata=metadata
        )

        return jsonify({
            'message': 'Transcription completed successfully',
            'full_transcript': result['full_transcript'],
            'segments': result['segments'],
            'speakers': result['speakers'],
            'confidence': result['confidence'],
            'transcript_file': result['transcript_file'],
            'metadata': result['metadata']
        }), 200

    except TranscriptionError as e:
        logger.error(f"Transcription error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in transcription: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_transcript():
    """
    Analyze transcript using Gemini AI

    Request JSON:
        - transcript: Full transcript text or path to transcript file
        - metadata: Meeting metadata (optional)

    Response:
        - action_items: Extracted action items
        - decisions: Key decisions made
        - key_topics: Topics discussed
        - open_questions: Unresolved questions
        - implicit_commitments: Implicit commitments
        - executive_summary: Executive summary
    """
    try:
        data = request.get_json()

        if not data or 'transcript' not in data:
            return jsonify({'error': 'transcript is required'}), 400

        transcript = data['transcript']

        # Check if transcript is a file path
        if isinstance(transcript, str) and os.path.exists(transcript):
            with open(transcript, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
                transcript = transcript_data.get('full_transcript', transcript)

        metadata = data.get('metadata', {})

        # Analyze transcript
        logger.info("Starting transcript analysis...")
        analysis = gemini_agent.analyze_transcript(transcript, metadata)

        return jsonify({
            'message': 'Analysis completed successfully',
            'analysis': analysis
        }), 200

    except GeminiAgentError as e:
        logger.error(f"Gemini agent error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in analysis: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/generate-minutes', methods=['POST'])
def generate_minutes():
    """
    Generate meeting minutes in specified formats

    Request JSON:
        - meeting_data: Meeting metadata and information
        - analysis: Analysis results from Gemini
        - template: Template type ('MRS', 'MTQP', 'MSAD')
        - formats: List of formats to generate (pdf, markdown, txt, docx)

    Response:
        - files: Dictionary mapping format to file path
    """
    try:
        data = request.get_json()

        if not data or 'meeting_data' not in data or 'analysis' not in data:
            return jsonify({'error': 'meeting_data and analysis are required'}), 400

        meeting_data = data['meeting_data']
        analysis = data['analysis']
        template = data.get('template', 'MRS')
        formats = data.get('formats', ['pdf', 'markdown'])

        # Generate minutes
        logger.info(f"Generating minutes in {template} format...")
        output_files = document_generator.generate_minutes(
            meeting_data,
            analysis,
            template=template,
            formats=formats
        )

        return jsonify({
            'message': 'Minutes generated successfully',
            'files': output_files,
            'template': template
        }), 200

    except DocumentGenerationError as e:
        logger.error(f"Document generation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in generation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/process-meeting', methods=['POST'])
def process_meeting():
    """
    End-to-end processing: upload -> transcribe -> analyze -> generate minutes

    Request:
        - file: Audio file (multipart/form-data)
        - metadata: JSON string with meeting metadata
        - template: Template type (default: MRS)
        - formats: Comma-separated list of formats (default: pdf,markdown)
        - enable_diarization: Enable speaker diarization (default: true)

    Response:
        - transcript_file: Path to transcript JSON
        - analysis: Analysis results
        - minutes_files: Dictionary of generated minutes files
    """
    try:
        # Step 1: Upload and validate audio
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
        enable_diarization = request.form.get('enable_diarization', 'true').lower() == 'true'

        # Save and validate file
        filename = secure_filename(file.filename)
        file_path = audio_processor.save_uploaded_file(file, filename)
        audio_metadata = audio_processor.validate_audio_file(file_path)

        logger.info(f"Processing meeting: {filename}")

        # Step 2: Convert to WAV if needed
        if not file_path.lower().endswith('.wav'):
            file_path = audio_processor.convert_to_wav(file_path)

        # Step 3: Transcribe
        logger.info("Transcribing audio...")
        transcript_result = transcription_service.transcribe_audio(
            file_path,
            enable_diarization=enable_diarization,
            metadata=meeting_metadata
        )

        # Step 4: Analyze with Gemini
        logger.info("Analyzing transcript...")
        analysis = gemini_agent.analyze_transcript(
            transcript_result['full_transcript'],
            meeting_metadata
        )

        # Step 5: Generate minutes
        logger.info("Generating minutes...")
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
            'message': 'Meeting processed successfully',
            'transcript_file': transcript_result['transcript_file'],
            'transcript': transcript_result['full_transcript'],
            'segments': transcript_result['segments'],
            'speakers': transcript_result['speakers'],
            'analysis': analysis,
            'minutes_files': minutes_files
        }), 200

    except (AudioProcessingError, TranscriptionError, GeminiAgentError, DocumentGenerationError) as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in processing: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/update-speakers', methods=['POST'])
def update_speaker_labels():
    """
    Update speaker labels in transcript

    Request JSON:
        - transcript_file: Path to transcript JSON file
        - speaker_mapping: Dictionary mapping speaker tags to names
                          e.g., {"Speaker 1": "John Doe", "Speaker 2": "Jane Smith"}

    Response:
        - message: Success message
        - updated_transcript: Updated transcript data
    """
    try:
        data = request.get_json()

        if not data or 'transcript_file' not in data or 'speaker_mapping' not in data:
            return jsonify({'error': 'transcript_file and speaker_mapping are required'}), 400

        transcript_file = data['transcript_file']
        speaker_mapping = data['speaker_mapping']

        # Update speaker labels
        updated_transcript = transcription_service.update_speaker_labels(
            transcript_file,
            speaker_mapping
        )

        return jsonify({
            'message': 'Speaker labels updated successfully',
            'transcript_file': transcript_file,
            'updated_speakers': updated_transcript['speakers']
        }), 200

    except Exception as e:
        logger.error(f"Error updating speaker labels: {str(e)}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """
    Download generated files

    Args:
        filename: Name of the file to download

    Returns:
        File download
    """
    try:
        # Check in exports folder
        file_path = config.EXPORT_FOLDER / filename

        if not file_path.exists():
            # Check in transcripts folder
            file_path = config.TRANSCRIPT_FOLDER / filename

        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/custom-query', methods=['POST'])
def custom_query():
    """
    Answer custom question about meeting transcript

    Request JSON:
        - transcript: Transcript text or file path
        - query: Question to answer

    Response:
        - answer: Answer to the query
    """
    try:
        data = request.get_json()

        if not data or 'transcript' not in data or 'query' not in data:
            return jsonify({'error': 'transcript and query are required'}), 400

        transcript = data['transcript']
        query = data['query']

        # Load transcript if file path
        if isinstance(transcript, str) and os.path.exists(transcript):
            with open(transcript, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
                transcript = transcript_data.get('full_transcript', transcript)

        # Get answer from Gemini
        answer = gemini_agent.generate_custom_query(transcript, query)

        return jsonify({
            'query': query,
            'answer': answer
        }), 200

    except Exception as e:
        logger.error(f"Error processing custom query: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting Meeting Minutes Generator API on port {port}")
    logger.info(f"Environment: {config_name}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
