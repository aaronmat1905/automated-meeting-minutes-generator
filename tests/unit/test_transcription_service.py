import json
from pathlib import Path

import pytest

from src.services.transcription_service import TranscriptionService
from src.config import get_config


def make_service_no_init():
    # Create instance without calling __init__ to avoid external dependencies
    svc = TranscriptionService.__new__(TranscriptionService)
    cfg = get_config('testing')
    svc.config = cfg
    svc.transcript_folder = cfg.TRANSCRIPT_FOLDER
    return svc


def test_create_speaker_segments_and_extract_info():
    svc = make_service_no_init()

    # sample words with speaker tags
    words = [
        {'word': 'Hello', 'start_time': 0.0, 'end_time': 0.5, 'speaker': 'Speaker 1'},
        {'word': 'this', 'start_time': 0.6, 'end_time': 0.8, 'speaker': 'Speaker 1'},
        {'word': 'is', 'start_time': 0.9, 'end_time': 1.0, 'speaker': 'Speaker 2'},
        {'word': 'a', 'start_time': 1.1, 'end_time': 1.2, 'speaker': 'Speaker 2'},
        {'word': 'test', 'start_time': 1.3, 'end_time': 1.6, 'speaker': 'Speaker 1'},
    ]

    segments = svc._create_speaker_segments(words)

    assert isinstance(segments, list)
    assert len(segments) == 3
    assert segments[0]['speaker'] == 'Speaker 1'
    assert 'Hello' in segments[0]['text']

    info = svc._extract_speaker_info(segments)
    assert 'Speaker 1' in info
    assert 'Speaker 2' in info
    assert info['Speaker 1']['word_count'] >= 1


def test_save_and_update_transcript(tmp_path):
    svc = make_service_no_init()
    sample = {
        'full_transcript': 'Hello world',
        'words': [],
        'segments': [],
        'speakers': {},
        'confidence': 0.9
    }

    # override transcript folder to tmp
    svc.transcript_folder = tmp_path

    path = svc._save_transcript(sample, 'sample_audio')
    assert Path(path).exists()

    # update labels via update_speaker_labels flow
    # prepare a minimal transcript with segments and speakers
    transcript = {
        'segments': [
            {'speaker': 'Speaker 1', 'text': 'Hi', 'start_time': 0.0, 'end_time': 0.5, 'words': []}
        ],
        'speakers': {'Speaker 1': {'name': 'Speaker 1', 'label': 'Speaker 1', 'total_duration': 0.5, 'segment_count': 1, 'word_count': 1}}
    }

    tf = tmp_path / 'to_update.json'
    tf.write_text(json.dumps(transcript))

    updated = svc.update_speaker_labels(str(tf), {'Speaker 1': 'Preetham'})
    assert 'Preetham' in updated['speakers']
