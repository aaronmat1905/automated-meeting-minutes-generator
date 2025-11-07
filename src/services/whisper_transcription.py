"""
Local Whisper Transcription Service
Runs transcription locally without requiring Google Cloud
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime
import whisper

from src.config import Config

logger = logging.getLogger(__name__)


class WhisperTranscriptionError(Exception):
    """Custom exception for transcription errors"""
    pass


class WhisperTranscriptionService:
    """Service for transcribing audio files using local Whisper model"""

    def __init__(self, config: Config, model_size: str = "base"):
        """
        Initialize Whisper transcription service

        Args:
            config: Application configuration
            model_size: Whisper model size (tiny, base, small, medium, large)
                       - tiny: Fastest, least accurate
                       - base: Good balance (recommended for low resources)
                       - small: Better accuracy
                       - medium/large: Best accuracy but slower
        """
        self.config = config
        self.transcript_folder = config.TRANSCRIPT_FOLDER
        self.model_size = model_size

        logger.info(f"Loading Whisper model: {model_size}")
        try:
            self.model = whisper.load_model(model_size)
            logger.info(f"Whisper model '{model_size}' loaded successfully")
        except Exception as e:
            raise WhisperTranscriptionError(f"Failed to load Whisper model: {str(e)}")

    def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "en",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Transcribe audio file using Whisper

        Args:
            audio_file_path: Path to audio file
            language: Language code (default: en)
            metadata: Additional meeting metadata

        Returns:
            Dictionary containing transcript and metadata
        """
        audio_file_path = Path(audio_file_path)

        if not audio_file_path.exists():
            raise WhisperTranscriptionError(f"Audio file not found: {audio_file_path}")

        try:
            logger.info(f"Starting transcription of {audio_file_path.name}...")

            # Transcribe with Whisper
            result = self.model.transcribe(
                str(audio_file_path),
                language=language,
                word_timestamps=True,
                verbose=False
            )

            # Process results
            processed_result = self._process_whisper_result(result)

            # Add metadata
            processed_result['metadata'] = metadata or {}
            processed_result['metadata']['audio_file'] = audio_file_path.name
            processed_result['metadata']['transcription_date'] = datetime.utcnow().isoformat()
            processed_result['metadata']['language'] = language
            processed_result['metadata']['model'] = self.model_size

            # Save transcript
            transcript_path = self._save_transcript(processed_result, audio_file_path.stem)
            processed_result['transcript_file'] = transcript_path

            logger.info(f"Transcription completed successfully")
            return processed_result

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise WhisperTranscriptionError(f"Failed to transcribe audio: {str(e)}")

    def _process_whisper_result(self, result: Dict) -> Dict:
        """
        Process Whisper transcription result

        Args:
            result: Raw Whisper result

        Returns:
            Processed result dictionary
        """
        processed = {
            'full_transcript': result['text'].strip(),
            'language': result.get('language', 'unknown'),
            'segments': [],
            'words': []
        }

        # Process segments
        for segment in result.get('segments', []):
            segment_data = {
                'id': segment['id'],
                'text': segment['text'].strip(),
                'start_time': segment['start'],
                'end_time': segment['end'],
                'confidence': segment.get('confidence', 0.0)
            }
            processed['segments'].append(segment_data)

            # Process words if available
            if 'words' in segment:
                for word in segment['words']:
                    word_data = {
                        'word': word['word'].strip(),
                        'start_time': word['start'],
                        'end_time': word['end'],
                        'confidence': word.get('probability', 0.0)
                    }
                    processed['words'].append(word_data)

        return processed

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

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return [
            'en',  # English
            'es',  # Spanish
            'fr',  # French
            'de',  # German
            'it',  # Italian
            'pt',  # Portuguese
            'nl',  # Dutch
            'pl',  # Polish
            'ru',  # Russian
            'zh',  # Chinese
            'ja',  # Japanese
            'ko',  # Korean
            'ar',  # Arabic
            'hi',  # Hindi
        ]
