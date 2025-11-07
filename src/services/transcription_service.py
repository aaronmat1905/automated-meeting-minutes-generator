"""
Google Speech-to-Text Transcription Service
Handles audio transcription with speaker diarization
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime

from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage
from google.oauth2 import service_account

from src.config import Config

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Custom exception for transcription errors"""
    pass


class TranscriptionService:
    """Service for transcribing audio files using Google Speech-to-Text"""

    def __init__(self, config: Config):
        self.config = config
        self.transcript_folder = config.TRANSCRIPT_FOLDER

        # Initialize Google Cloud clients
        if config.GOOGLE_APPLICATION_CREDENTIALS:
            credentials = service_account.Credentials.from_service_account_file(
                config.GOOGLE_APPLICATION_CREDENTIALS
            )
            self.speech_client = speech.SpeechClient(credentials=credentials)
            self.storage_client = storage.Client(
                credentials=credentials,
                project=config.GOOGLE_CLOUD_PROJECT_ID
            )
        else:
            # Use default credentials (for Cloud environments)
            self.speech_client = speech.SpeechClient()
            self.storage_client = storage.Client(project=config.GOOGLE_CLOUD_PROJECT_ID)

    def transcribe_audio(
        self,
        audio_file_path: str,
        enable_diarization: bool = True,
        language_code: str = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Transcribe audio file with speaker diarization

        Args:
            audio_file_path: Path to audio file
            enable_diarization: Enable speaker diarization
            language_code: Language code (default from config)
            metadata: Additional meeting metadata

        Returns:
            Dictionary containing transcript and metadata
        """
        if language_code is None:
            language_code = self.config.GOOGLE_SPEECH_LANGUAGE_CODE

        audio_file_path = Path(audio_file_path)

        if not audio_file_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_file_path}")

        try:
            # Check file size to determine processing method
            file_size_mb = audio_file_path.stat().st_size / (1024 * 1024)

            if file_size_mb < 10:
                # Use synchronous recognition for small files
                logger.info(f"Using synchronous recognition for {audio_file_path.name}")
                result = self._transcribe_sync(audio_file_path, enable_diarization, language_code)
            else:
                # Use asynchronous recognition for large files
                logger.info(f"Using asynchronous recognition for {audio_file_path.name}")
                result = self._transcribe_async(audio_file_path, enable_diarization, language_code)

            # Add metadata
            result['metadata'] = metadata or {}
            result['metadata']['audio_file'] = audio_file_path.name
            result['metadata']['transcription_date'] = datetime.utcnow().isoformat()
            result['metadata']['language_code'] = language_code
            result['metadata']['diarization_enabled'] = enable_diarization

            # Save transcript to file
            transcript_path = self._save_transcript(result, audio_file_path.stem)
            result['transcript_file'] = transcript_path

            logger.info(f"Transcription completed successfully for {audio_file_path.name}")
            return result

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise TranscriptionError(f"Failed to transcribe audio: {str(e)}")

    def _transcribe_sync(
        self,
        audio_file_path: Path,
        enable_diarization: bool,
        language_code: str
    ) -> Dict:
        """
        Synchronous transcription for files < 10MB

        Args:
            audio_file_path: Path to audio file
            enable_diarization: Enable speaker diarization
            language_code: Language code

        Returns:
            Transcription result dictionary
        """
        # Read audio file
        with open(audio_file_path, 'rb') as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)

        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.config.GOOGLE_SPEECH_SAMPLE_RATE_HERTZ,
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            model='latest_long',
            use_enhanced=True,
        )

        # Configure speaker diarization
        if enable_diarization:
            diarization_config = speech.SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=2,
                max_speaker_count=self.config.GOOGLE_SPEECH_MAX_SPEAKER_COUNT,
            )
            config.diarization_config = diarization_config

        # Perform recognition
        response = self.speech_client.recognize(config=config, audio=audio)

        return self._process_response(response, enable_diarization)

    def _transcribe_async(
        self,
        audio_file_path: Path,
        enable_diarization: bool,
        language_code: str
    ) -> Dict:
        """
        Asynchronous transcription for large files (>10MB)

        Args:
            audio_file_path: Path to audio file
            enable_diarization: Enable speaker diarization
            language_code: Language code

        Returns:
            Transcription result dictionary
        """
        # Upload to Google Cloud Storage
        gcs_uri = self._upload_to_gcs(audio_file_path)

        audio = speech.RecognitionAudio(uri=gcs_uri)

        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.config.GOOGLE_SPEECH_SAMPLE_RATE_HERTZ,
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            model='latest_long',
            use_enhanced=True,
        )

        # Configure speaker diarization
        if enable_diarization:
            diarization_config = speech.SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=2,
                max_speaker_count=self.config.GOOGLE_SPEECH_MAX_SPEAKER_COUNT,
            )
            config.diarization_config = diarization_config

        # Start async operation
        operation = self.speech_client.long_running_recognize(config=config, audio=audio)

        logger.info("Waiting for transcription to complete...")
        response = operation.result(timeout=self.config.TRANSCRIPTION_TIMEOUT_SECONDS)

        return self._process_response(response, enable_diarization)

    def _process_response(
        self,
        response,
        enable_diarization: bool
    ) -> Dict:
        """
        Process Google Speech-to-Text response

        Args:
            response: Speech recognition response
            enable_diarization: Whether diarization was enabled

        Returns:
            Processed transcription result
        """
        result = {
            'full_transcript': '',
            'words': [],
            'segments': [],
            'speakers': {},
            'confidence': 0.0
        }

        if not response.results:
            logger.warning("No transcription results returned")
            return result

        # Process results
        total_confidence = 0
        word_count = 0

        for result_item in response.results:
            alternative = result_item.alternatives[0]

            # Add to full transcript
            result['full_transcript'] += alternative.transcript + ' '

            # Process words with timestamps
            for word_info in alternative.words:
                word_data = {
                    'word': word_info.word,
                    'start_time': word_info.start_time.total_seconds(),
                    'end_time': word_info.end_time.total_seconds(),
                    'confidence': alternative.confidence
                }

                # Add speaker tag if diarization enabled
                if enable_diarization and hasattr(word_info, 'speaker_tag'):
                    word_data['speaker'] = f"Speaker {word_info.speaker_tag}"

                result['words'].append(word_data)
                total_confidence += alternative.confidence
                word_count += 1

        # Calculate average confidence
        if word_count > 0:
            result['confidence'] = total_confidence / len(response.results)

        # Clean up transcript
        result['full_transcript'] = result['full_transcript'].strip()

        # Create speaker segments if diarization enabled
        if enable_diarization and result['words']:
            result['segments'] = self._create_speaker_segments(result['words'])
            result['speakers'] = self._extract_speaker_info(result['segments'])

        return result

    def _create_speaker_segments(self, words: List[Dict]) -> List[Dict]:
        """
        Create segments grouped by speaker

        Args:
            words: List of word dictionaries with speaker tags

        Returns:
            List of speaker segments
        """
        segments = []
        current_segment = None

        for word in words:
            speaker = word.get('speaker', 'Unknown')

            # Start new segment if speaker changes
            if current_segment is None or current_segment['speaker'] != speaker:
                if current_segment:
                    segments.append(current_segment)

                current_segment = {
                    'speaker': speaker,
                    'text': word['word'],
                    'start_time': word['start_time'],
                    'end_time': word['end_time'],
                    'words': [word]
                }
            else:
                # Continue current segment
                current_segment['text'] += ' ' + word['word']
                current_segment['end_time'] = word['end_time']
                current_segment['words'].append(word)

        # Add last segment
        if current_segment:
            segments.append(current_segment)

        return segments

    def _extract_speaker_info(self, segments: List[Dict]) -> Dict:
        """
        Extract speaker statistics from segments

        Args:
            segments: List of speaker segments

        Returns:
            Dictionary of speaker information
        """
        speaker_info = {}

        for segment in segments:
            speaker = segment['speaker']

            if speaker not in speaker_info:
                speaker_info[speaker] = {
                    'name': speaker,
                    'label': speaker,
                    'total_duration': 0,
                    'segment_count': 0,
                    'word_count': 0
                }

            duration = segment['end_time'] - segment['start_time']
            speaker_info[speaker]['total_duration'] += duration
            speaker_info[speaker]['segment_count'] += 1
            speaker_info[speaker]['word_count'] += len(segment['words'])

        return speaker_info

    def _upload_to_gcs(self, file_path: Path) -> str:
        """
        Upload file to Google Cloud Storage

        Args:
            file_path: Path to file to upload

        Returns:
            GCS URI
        """
        bucket_name = self.config.GCS_BUCKET_NAME
        if not bucket_name:
            raise TranscriptionError("GCS_BUCKET_NAME not configured")

        bucket = self.storage_client.bucket(bucket_name)
        blob_name = f"{self.config.GCS_AUDIO_FOLDER}/{file_path.name}"
        blob = bucket.blob(blob_name)

        logger.info(f"Uploading {file_path.name} to GCS...")
        blob.upload_from_filename(str(file_path))

        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        logger.info(f"File uploaded to {gcs_uri}")

        return gcs_uri

    def _save_transcript(self, transcript_data: Dict, base_name: str) -> str:
        """
        Save transcript to JSON file

        Args:
            transcript_data: Transcript data dictionary
            base_name: Base name for the file

        Returns:
            Path to saved transcript file
        """
        self.transcript_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_transcript_{timestamp}.json"
        file_path = self.transcript_folder / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Transcript saved to {file_path}")
        return str(file_path)

    def update_speaker_labels(
        self,
        transcript_file: str,
        speaker_mapping: Dict[str, str]
    ) -> Dict:
        """
        Update speaker labels in transcript

        Args:
            transcript_file: Path to transcript JSON file
            speaker_mapping: Dictionary mapping speaker tags to names
                            e.g., {"Speaker 1": "John Doe", "Speaker 2": "Jane Smith"}

        Returns:
            Updated transcript data
        """
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        # Update speaker labels in segments
        for segment in transcript_data.get('segments', []):
            old_speaker = segment['speaker']
            if old_speaker in speaker_mapping:
                segment['speaker'] = speaker_mapping[old_speaker]

        # Update speaker info
        if 'speakers' in transcript_data:
            new_speakers = {}
            for old_speaker, info in transcript_data['speakers'].items():
                new_speaker = speaker_mapping.get(old_speaker, old_speaker)
                info['name'] = new_speaker
                info['label'] = new_speaker
                new_speakers[new_speaker] = info
            transcript_data['speakers'] = new_speakers

        # Save updated transcript
        with open(transcript_file, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Updated speaker labels in {transcript_file}")
        return transcript_data
