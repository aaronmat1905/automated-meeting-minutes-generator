"""
AssemblyAI Transcription Service
Simple, fast, accurate transcription with FREE tier!
"""

import logging
from typing import Dict, Optional
from pathlib import Path
import json
from datetime import datetime
import assemblyai as aai

from src.config_simple import Config

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Custom exception for transcription errors"""
    pass


class AssemblyAITranscriptionService:
    """Service for transcribing audio using AssemblyAI"""

    def __init__(self, config: Config):
        """
        Initialize AssemblyAI transcription service

        Args:
            config: Application configuration
        """
        self.config = config
        self.transcript_folder = config.TRANSCRIPT_FOLDER

        # Check API key
        api_key = config.ASSEMBLYAI_API_KEY
        if not api_key:
            raise TranscriptionError(
                "ASSEMBLYAI_API_KEY not configured. "
                "Get your free API key from: https://www.assemblyai.com/dashboard/signup"
            )

        # Configure AssemblyAI
        aai.settings.api_key = api_key
        logger.info("AssemblyAI transcription service initialized")

    def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "en",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Transcribe audio file using AssemblyAI

        Args:
            audio_file_path: Path to audio file
            language: Language code (default: en)
            metadata: Additional meeting metadata

        Returns:
            Dictionary containing transcript and metadata
        """
        audio_file_path = Path(audio_file_path)

        if not audio_file_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_file_path}")

        try:
            logger.info(f"Starting transcription of {audio_file_path.name}...")

            # Configure transcription
            config = aai.TranscriptionConfig(
                language_code=language,
                punctuate=True,
                format_text=True,
                speaker_labels=False,  # Set to True if you want speaker diarization
            )

            # Create transcriber
            transcriber = aai.Transcriber()

            # Upload and transcribe
            logger.info("Uploading audio to AssemblyAI...")
            transcript = transcriber.transcribe(str(audio_file_path), config=config)

            # Check for errors
            if transcript.status == aai.TranscriptStatus.error:
                raise TranscriptionError(f"Transcription failed: {transcript.error}")

            # Process results
            result = self._process_transcript(transcript)

            # Add metadata
            result['metadata'] = metadata or {}
            result['metadata']['audio_file'] = audio_file_path.name
            result['metadata']['transcription_date'] = datetime.utcnow().isoformat()
            result['metadata']['language'] = language
            result['metadata']['service'] = 'AssemblyAI'

            # Save transcript
            transcript_path = self._save_transcript(result, audio_file_path.stem)
            result['transcript_file'] = transcript_path

            logger.info(f"Transcription completed successfully!")
            return result

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise TranscriptionError(f"Failed to transcribe audio: {str(e)}")

    def _process_transcript(self, transcript) -> Dict:
        """
        Process AssemblyAI transcript result

        Args:
            transcript: AssemblyAI transcript object

        Returns:
            Processed result dictionary
        """
        result = {
            'full_transcript': transcript.text,
            'language': getattr(transcript, 'language_code', 'en'),  # Safe access
            'confidence': transcript.confidence if hasattr(transcript, 'confidence') else 0.0,
            'audio_duration': transcript.audio_duration if hasattr(transcript, 'audio_duration') else 0,
            'words': [],
            'segments': []
        }

        # Process words with timestamps
        if transcript.words:
            for word in transcript.words:
                word_data = {
                    'word': word.text,
                    'start_time': word.start / 1000.0,  # Convert ms to seconds
                    'end_time': word.end / 1000.0,
                    'confidence': word.confidence
                }
                result['words'].append(word_data)

        # Create segments (sentences)
        if transcript.utterances:
            for utterance in transcript.utterances:
                segment = {
                    'text': utterance.text,
                    'start_time': utterance.start / 1000.0,
                    'end_time': utterance.end / 1000.0,
                    'confidence': utterance.confidence,
                    'words': utterance.words
                }
                result['segments'].append(segment)
        elif transcript.words:
            # If no utterances, create segments from sentences
            result['segments'] = self._create_segments_from_words(result['words'], transcript.text)

        return result

    def _create_segments_from_words(self, words: list, full_text: str) -> list:
        """Create segments by splitting on sentence boundaries"""
        segments = []
        sentences = full_text.split('. ')

        current_word_idx = 0
        for sentence in sentences:
            if not sentence.strip():
                continue

            sentence_words = sentence.strip().split()
            num_words = len(sentence_words)

            if current_word_idx + num_words <= len(words):
                segment_words = words[current_word_idx:current_word_idx + num_words]

                if segment_words:
                    segment = {
                        'text': sentence.strip() + '.',
                        'start_time': segment_words[0]['start_time'],
                        'end_time': segment_words[-1]['end_time'],
                        'confidence': sum(w['confidence'] for w in segment_words) / len(segment_words),
                        'words': segment_words
                    }
                    segments.append(segment)

                current_word_idx += num_words

        return segments

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

    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'hi', 'ja',
            'zh', 'fi', 'ko', 'pl', 'ru', 'tr', 'uk', 'vi'
        ]
