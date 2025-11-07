"""
Unit tests for Audio Processor service
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.services.audio_processor import AudioProcessor, AudioProcessingError
from src.config import DevelopmentConfig


@pytest.fixture
def config():
    """Create test configuration"""
    return DevelopmentConfig


@pytest.fixture
def audio_processor(config):
    """Create AudioProcessor instance"""
    return AudioProcessor(config)


@pytest.fixture
def temp_audio_file():
    """Create temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(b'fake audio content')
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestAudioProcessor:
    """Test cases for AudioProcessor"""

    def test_initialization(self, audio_processor, config):
        """Test AudioProcessor initialization"""
        assert audio_processor.config == config
        assert audio_processor.upload_folder == config.UPLOAD_FOLDER
        assert audio_processor.allowed_formats == config.ALLOWED_AUDIO_FORMATS
        assert audio_processor.max_file_size == config.MAX_AUDIO_FILE_SIZE_BYTES

    def test_validate_audio_file_not_found(self, audio_processor):
        """Test validation with non-existent file"""
        with pytest.raises(AudioProcessingError, match="Audio file not found"):
            audio_processor.validate_audio_file('/nonexistent/file.mp3')

    @patch('src.services.audio_processor.AudioSegment')
    def test_validate_audio_file_success(self, mock_audio_segment, audio_processor, temp_audio_file):
        """Test successful audio file validation"""
        # Mock AudioSegment
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 60000  # 60 seconds
        mock_audio.channels = 2
        mock_audio.frame_rate = 44100
        mock_audio.sample_width = 2
        mock_audio_segment.from_file.return_value = mock_audio

        result = audio_processor.validate_audio_file(temp_audio_file)

        assert result['valid'] is True
        assert 'file_path' in result
        assert 'file_name' in result
        assert 'duration_seconds' in result
        assert result['duration_seconds'] == 60.0

    def test_validate_audio_file_too_large(self, audio_processor, config):
        """Test validation with file exceeding size limit"""
        # Create a mock file that appears too large
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            # Write data larger than max size
            f.write(b'x' * (config.MAX_AUDIO_FILE_SIZE_BYTES + 1000))
            large_file = f.name

        try:
            with pytest.raises(AudioProcessingError, match="exceeds maximum"):
                audio_processor.validate_audio_file(large_file)
        finally:
            os.unlink(large_file)

    def test_validate_audio_file_unsupported_format(self, audio_processor):
        """Test validation with unsupported format"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'fake content')
            unsupported_file = f.name

        try:
            with pytest.raises(AudioProcessingError, match="Unsupported audio format"):
                audio_processor.validate_audio_file(unsupported_file)
        finally:
            os.unlink(unsupported_file)

    @patch('src.services.audio_processor.AudioSegment')
    def test_convert_to_wav(self, mock_audio_segment, audio_processor, temp_audio_file):
        """Test audio conversion to WAV"""
        mock_audio = MagicMock()
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.export = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio

        output_path = audio_processor.convert_to_wav(temp_audio_file)

        assert output_path.endswith('.wav')
        mock_audio.set_channels.assert_called_once_with(1)  # Mono
        mock_audio.set_frame_rate.assert_called_once_with(16000)  # 16kHz
        mock_audio.export.assert_called_once()

    def test_save_uploaded_file(self, audio_processor):
        """Test saving uploaded file"""
        # Create mock file object
        mock_file = MagicMock()
        mock_file.save = MagicMock()

        filename = 'test_audio.mp3'
        result_path = audio_processor.save_uploaded_file(mock_file, filename)

        assert filename in result_path
        mock_file.save.assert_called_once()

    @patch('src.services.audio_processor.AudioSegment')
    def test_split_audio_chunks(self, mock_audio_segment, audio_processor, temp_audio_file):
        """Test splitting audio into chunks"""
        # Mock audio of 180 seconds (3 minutes)
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 180000  # 180 seconds in ms
        mock_audio.__getitem__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio

        chunks = audio_processor.split_audio_chunks(temp_audio_file, chunk_duration_ms=60000)

        # Should create 3 chunks for 180 second audio
        assert len(chunks) == 3
        for chunk_path in chunks:
            assert 'chunk' in chunk_path

    @patch('src.services.audio_processor.librosa')
    def test_check_audio_quality_low_snr(self, mock_librosa, audio_processor, temp_audio_file):
        """Test audio quality check with low SNR"""
        # Mock librosa to simulate low SNR audio
        import numpy as np
        mock_librosa.load.return_value = (np.random.rand(16000) * 0.01, 16000)  # Very quiet
        mock_librosa.to_mono.return_value = np.random.rand(16000) * 0.01
        mock_librosa.feature.rms.return_value = np.array([[0.001, 0.002, 0.001]])

        issues = audio_processor._check_audio_quality(temp_audio_file)

        # Should detect low SNR or silence
        assert len(issues) > 0

    def test_cleanup_temp_files(self, audio_processor):
        """Test cleanup of temporary files"""
        # Create temporary test files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(b'test')
                temp_files.append(f.name)

        # Cleanup files
        audio_processor.cleanup_temp_files(temp_files)

        # Verify files are deleted
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
