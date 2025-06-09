# services/input_processor/tests/test_input_processor.py

"""Dummy tests for the InputProcessor component."""

import uuid

from services.input_processor.src.input_processor import InputProcessor


def test_input_processor_initialization() -> None:
    """Tests that the InputProcessor can be initialized without errors."""
    processor = InputProcessor()
    assert processor is not None


def test_process_text_input_dummy_returns_success_false() -> None:
    """Tests the dummy implementation of process_text_input returns success=False."""
    processor = InputProcessor()
    device_id = uuid.uuid4()
    result = processor.process_text_input("hello", device_id)
    assert result["success"] is False
    assert result["processed_text"] == "hello"
    assert "turn_id" in result
    assert "conversation_id" in result
    assert "user_id" in result


def test_process_audio_input_dummy_returns_success_false() -> None:
    """Tests the dummy implementation of process_audio_input returns success=False."""
    processor = InputProcessor()
    device_id = uuid.uuid4()
    raw_audio = b"some_audio_data"
    result = processor.process_audio_input(raw_audio, device_id)
    assert result["success"] is False
    assert "processed_text" in result
    assert "turn_id" in result
    assert "conversation_id" in result
    assert "user_id" in result
