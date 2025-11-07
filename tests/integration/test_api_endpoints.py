"""
Integration tests for Flask API endpoints
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.app import app
from src.config import TestingConfig


@pytest.fixture
def client():
    """Create Flask test client"""
    app.config.from_object(TestingConfig)
    TestingConfig.init_app(app)

    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_audio_file():
    """Create sample audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(b'fake audio content for testing')
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_transcript():
    """Sample transcript data"""
    return {
        "full_transcript": "This is a test meeting transcript.",
        "segments": [
            {
                "speaker": "Speaker 1",
                "text": "Hello everyone.",
                "start_time": 0.0,
                "end_time": 2.0
            }
        ],
        "speakers": {
            "Speaker 1": {
                "name": "Speaker 1",
                "total_duration": 2.0,
                "segment_count": 1
            }
        },
        "confidence": 0.95
    }


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'version' in data


class TestUploadEndpoint:
    """Tests for audio upload endpoint"""

    @patch('src.services.audio_processor.AudioProcessor.validate_audio_file')
    def test_upload_audio_success(self, mock_validate, client, sample_audio_file):
        """Test successful audio upload"""
        mock_validate.return_value = {
            'valid': True,
            'file_name': 'test.mp3',
            'file_size_mb': 0.1,
            'duration_seconds': 60.0
        }

        with open(sample_audio_file, 'rb') as f:
            data = {
                'file': (f, 'test.mp3'),
                'metadata': json.dumps({
                    'title': 'Test Meeting',
                    'participants': ['Alice', 'Bob']
                })
            }

            response = client.post(
                '/api/upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'file_id' in response_data
        assert 'file_path' in response_data

    def test_upload_no_file(self, client):
        """Test upload without file"""
        response = client.post('/api/upload')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data

    def test_upload_invalid_metadata(self, client, sample_audio_file):
        """Test upload with invalid metadata JSON"""
        with open(sample_audio_file, 'rb') as f:
            data = {
                'file': (f, 'test.mp3'),
                'metadata': 'invalid json'
            }

            response = client.post(
                '/api/upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 400


class TestTranscribeEndpoint:
    """Tests for transcription endpoint"""

    @patch('src.services.transcription_service.TranscriptionService.transcribe_audio')
    @patch('src.services.audio_processor.AudioProcessor.convert_to_wav')
    def test_transcribe_audio_success(self, mock_convert, mock_transcribe, client, sample_transcript):
        """Test successful transcription"""
        mock_convert.return_value = '/tmp/test.wav'
        sample_transcript['transcript_file'] = '/tmp/transcript.json'
        sample_transcript['metadata'] = {}
        mock_transcribe.return_value = sample_transcript

        data = {
            'file_path': '/tmp/test.mp3',
            'enable_diarization': True
        }

        response = client.post(
            '/api/transcribe',
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'full_transcript' in response_data
        assert 'segments' in response_data
        assert 'speakers' in response_data

    def test_transcribe_no_file_path(self, client):
        """Test transcription without file path"""
        response = client.post(
            '/api/transcribe',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400


class TestAnalyzeEndpoint:
    """Tests for transcript analysis endpoint"""

    @patch('src.services.gemini_agent.GeminiAgent.analyze_transcript')
    def test_analyze_transcript_success(self, mock_analyze, client):
        """Test successful transcript analysis"""
        mock_analyze.return_value = {
            'action_items': [
                {'description': 'Test action', 'owner': 'Alice', 'priority': 'high'}
            ],
            'decisions': [
                {'decision': 'Use GCP', 'rationale': 'Best fit'}
            ],
            'executive_summary': {
                'overview': 'Test meeting summary'
            }
        }

        data = {
            'transcript': 'This is a test transcript.',
            'metadata': {'title': 'Test Meeting'}
        }

        response = client.post(
            '/api/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'analysis' in response_data
        assert 'action_items' in response_data['analysis']

    def test_analyze_no_transcript(self, client):
        """Test analysis without transcript"""
        response = client.post(
            '/api/analyze',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400


class TestGenerateMinutesEndpoint:
    """Tests for minutes generation endpoint"""

    @patch('src.services.document_generator.DocumentGenerator.generate_minutes')
    def test_generate_minutes_success(self, mock_generate, client):
        """Test successful minutes generation"""
        mock_generate.return_value = {
            'pdf': '/tmp/minutes.pdf',
            'markdown': '/tmp/minutes.md'
        }

        data = {
            'meeting_data': {
                'title': 'Test Meeting',
                'date': '2025-11-06',
                'participants': ['Alice', 'Bob']
            },
            'analysis': {
                'action_items': [],
                'decisions': []
            },
            'template': 'MRS',
            'formats': ['pdf', 'markdown']
        }

        response = client.post(
            '/api/generate-minutes',
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'files' in response_data
        assert 'pdf' in response_data['files']

    def test_generate_minutes_missing_data(self, client):
        """Test minutes generation with missing data"""
        data = {'meeting_data': {}}

        response = client.post(
            '/api/generate-minutes',
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 400


class TestProcessMeetingEndpoint:
    """Tests for end-to-end meeting processing endpoint"""

    @patch('src.services.document_generator.DocumentGenerator.generate_minutes')
    @patch('src.services.gemini_agent.GeminiAgent.analyze_transcript')
    @patch('src.services.transcription_service.TranscriptionService.transcribe_audio')
    @patch('src.services.audio_processor.AudioProcessor.convert_to_wav')
    @patch('src.services.audio_processor.AudioProcessor.validate_audio_file')
    def test_process_meeting_end_to_end(
        self,
        mock_validate,
        mock_convert,
        mock_transcribe,
        mock_analyze,
        mock_generate,
        client,
        sample_audio_file,
        sample_transcript
    ):
        """Test complete meeting processing workflow"""
        # Setup mocks
        mock_validate.return_value = {
            'valid': True,
            'duration_minutes': 5.0
        }
        mock_convert.return_value = '/tmp/test.wav'

        sample_transcript['transcript_file'] = '/tmp/transcript.json'
        sample_transcript['metadata'] = {}
        mock_transcribe.return_value = sample_transcript

        mock_analyze.return_value = {
            'action_items': [],
            'decisions': [],
            'executive_summary': {'overview': 'Test'}
        }

        mock_generate.return_value = {
            'pdf': '/tmp/minutes.pdf'
        }

        # Make request
        with open(sample_audio_file, 'rb') as f:
            data = {
                'file': (f, 'test.mp3'),
                'metadata': json.dumps({
                    'title': 'Test Meeting',
                    'participants': ['Alice']
                }),
                'template': 'MRS',
                'formats': 'pdf'
            }

            response = client.post(
                '/api/process-meeting',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'transcript_file' in response_data
        assert 'analysis' in response_data
        assert 'minutes_files' in response_data


class TestUpdateSpeakersEndpoint:
    """Tests for speaker label update endpoint"""

    @patch('src.services.transcription_service.TranscriptionService.update_speaker_labels')
    def test_update_speakers_success(self, mock_update, client):
        """Test successful speaker label update"""
        mock_update.return_value = {
            'speakers': {
                'John Doe': {'name': 'John Doe'},
                'Jane Smith': {'name': 'Jane Smith'}
            }
        }

        data = {
            'transcript_file': '/tmp/transcript.json',
            'speaker_mapping': {
                'Speaker 1': 'John Doe',
                'Speaker 2': 'Jane Smith'
            }
        }

        response = client.post(
            '/api/update-speakers',
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'updated_speakers' in response_data

    def test_update_speakers_missing_data(self, client):
        """Test speaker update with missing data"""
        response = client.post(
            '/api/update-speakers',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400


class TestCustomQueryEndpoint:
    """Tests for custom query endpoint"""

    @patch('src.services.gemini_agent.GeminiAgent.generate_custom_query')
    def test_custom_query_success(self, mock_query, client):
        """Test successful custom query"""
        mock_query.return_value = "The meeting discussed project updates."

        data = {
            'transcript': 'Test transcript content.',
            'query': 'What was discussed?'
        }

        response = client.post(
            '/api/custom-query',
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'answer' in response_data
        assert len(response_data['answer']) > 0


class TestErrorHandlers:
    """Tests for error handlers"""

    def test_404_error(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
