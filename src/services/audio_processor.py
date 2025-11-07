"""
Audio Processing Service
Handles audio file upload, validation, and preprocessing
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional
from pydub import AudioSegment

try:
    import librosa
except Exception:
    # librosa is optional for the simplified local version
    librosa = None

try:
    from src.config_simple import Config
except ImportError:
    from src.config import Config

logger = logging.getLogger(__name__)


class AudioProcessingError(Exception):
    """Custom exception for audio processing errors"""
    pass


class AudioProcessor:
    """Service for processing and validating audio files"""

    def __init__(self, config: Config):
        self.config = config
        self.upload_folder = config.UPLOAD_FOLDER
        self.allowed_formats = config.ALLOWED_AUDIO_FORMATS
        self.max_file_size = config.MAX_AUDIO_FILE_SIZE_BYTES

    def validate_audio_file(self, file_path: str) -> Dict[str, any]:
        """
        Validate audio file format, size, and quality

        Args:
            file_path: Path to the audio file

        Returns:
            Dictionary containing validation results and audio metadata

        Raises:
            AudioProcessingError: If validation fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise AudioProcessingError(f"Audio file not found: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise AudioProcessingError(
                f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum "
                f"allowed size ({self.config.MAX_AUDIO_FILE_SIZE_MB} MB)"
            )

        # Check file format
        file_extension = file_path.suffix.lower().lstrip('.')
        if file_extension not in self.allowed_formats:
            raise AudioProcessingError(
                f"Unsupported audio format: {file_extension}. "
                f"Allowed formats: {', '.join(self.allowed_formats)}"
            )

        try:
            # Load audio metadata
            audio = AudioSegment.from_file(str(file_path))
            duration_seconds = len(audio) / 1000.0

            metadata = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size_mb': file_size / (1024 * 1024),
                'format': file_extension,
                'duration_seconds': duration_seconds,
                'duration_minutes': duration_seconds / 60.0,
                'channels': audio.channels,
                'sample_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'valid': True
            }

            # Skip quality check for simplified version (requires librosa)
            metadata['quality_issues'] = []
            metadata['has_quality_issues'] = False

            logger.info(f"Audio validation successful: {file_path.name}")
            return metadata

        except Exception as e:
            logger.error(f"Error validating audio file: {str(e)}")
            raise AudioProcessingError(f"Failed to validate audio file: {str(e)}")

    def _check_audio_quality(self, file_path: str) -> list:
        """
        Check audio quality and flag potential issues
        (Disabled in simplified version - requires librosa)

        Args:
            file_path: Path to the audio file

        Returns:
            List of quality issues found
        """
        issues = []

        # If librosa is not available, skip quality checks
        if not librosa:
            return issues

        try:
            # Use librosa to load and analyze audio
            y, sr = librosa.load(str(file_path), sr=None)
            # Convert to mono if necessary
            try:
                y_mono = librosa.to_mono(y)
            except Exception:
                y_mono = y

            # Compute RMS (root mean square) energy
            rms = librosa.feature.rms(y=y_mono)
            avg_rms = float(rms.mean()) if hasattr(rms, 'mean') else float(sum(rms[0]) / len(rms[0]))

            # Thresholds (tunable)
            SILENCE_RMS_THRESHOLD = 0.005
            LOW_SNR_THRESHOLD = 0.01

            if avg_rms <= SILENCE_RMS_THRESHOLD:
                issues.append('silence_or_near_silence')
            elif avg_rms <= LOW_SNR_THRESHOLD:
                issues.append('low_snr')

        except Exception as e:
            logger.debug(f"Audio quality check error: {str(e)}")

        return issues

    def convert_to_wav(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert audio file to WAV format for Google Speech-to-Text

        Args:
            input_path: Path to input audio file
            output_path: Path for output WAV file (optional)

        Returns:
            Path to converted WAV file
        """
        input_path = Path(input_path)

        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_converted.wav"
        else:
            output_path = Path(output_path)

        try:
            logger.info(f"Converting {input_path.name} to WAV format...")

            # Load audio
            audio = AudioSegment.from_file(str(input_path))

            # Convert to mono (Google Speech-to-Text works better with mono)
            audio = audio.set_channels(1)

            # Set sample rate to 16kHz (optimal for speech recognition)
            audio = audio.set_frame_rate(16000)

            # Export as WAV
            audio.export(str(output_path), format='wav')

            logger.info(f"Audio converted successfully: {output_path.name}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")
            raise AudioProcessingError(f"Failed to convert audio file: {str(e)}")

    def split_audio_chunks(self, file_path: str, chunk_duration_ms: int = 60000) -> list:
        """
        Split audio file into chunks for processing long recordings

        Args:
            file_path: Path to audio file
            chunk_duration_ms: Duration of each chunk in milliseconds (default: 60 seconds)

        Returns:
            List of chunk file paths
        """
        file_path = Path(file_path)

        try:
            audio = AudioSegment.from_file(str(file_path))
            chunks = []

            # Calculate number of chunks (use ceiling division)
            total_duration = len(audio)
            num_chunks = (total_duration + chunk_duration_ms - 1) // chunk_duration_ms

            logger.info(f"Splitting audio into {num_chunks} chunks...")

            for i in range(num_chunks):
                start = i * chunk_duration_ms
                end = min((i + 1) * chunk_duration_ms, total_duration)

                chunk = audio[start:end]
                chunk_path = file_path.parent / f"{file_path.stem}_chunk_{i+1}.wav"

                chunk.export(str(chunk_path), format='wav')
                chunks.append(str(chunk_path))

            logger.info(f"Audio split into {len(chunks)} chunks successfully")
            return chunks

        except Exception as e:
            logger.error(f"Error splitting audio: {str(e)}")
            raise AudioProcessingError(f"Failed to split audio file: {str(e)}")

    def save_uploaded_file(self, file, filename: str) -> str:
        """
        Save uploaded file to the upload folder

        Args:
            file: File object from request
            filename: Name for the saved file

        Returns:
            Path to saved file
        """
        try:
            # Ensure upload folder exists
            self.upload_folder.mkdir(parents=True, exist_ok=True)

            # Generate unique filename if file already exists
            file_path = self.upload_folder / filename
            if file_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                counter = 1
                while file_path.exists():
                    file_path = self.upload_folder / f"{stem}_{counter}{suffix}"
                    counter += 1

            # Save file
            file.save(str(file_path))
            logger.info(f"File saved successfully: {file_path}")

            return str(file_path)

        except Exception as e:
            logger.error(f"Error saving uploaded file: {str(e)}")
            raise AudioProcessingError(f"Failed to save uploaded file: {str(e)}")

    def cleanup_temp_files(self, file_paths: list):
        """
        Clean up temporary audio files

        Args:
            file_paths: List of file paths to delete
        """
        for file_path in file_paths:
            try:
                file_path = Path(file_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Deleted temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not delete temporary file {file_path}: {str(e)}")
