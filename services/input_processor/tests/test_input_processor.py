# services/input_processor/tests/test_input_processor.py

"""Unit tests for the InputProcessor component."""

import uuid
from unittest.mock import Mock

import pytest

from services.input_processor.src.input_processor import (
    InputProcessor,
    NLUProcessingError,
)
from services.nlu_service.src.nlu_service_interface import NLUServiceInterface

# Use a fixed UUID for consistent testing
TEST_DEVICE_ID = uuid.UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef")


@pytest.fixture
def mock_nlu_service():
    """Fixture that provides a mock NLUServiceInterface instance.

    We'll configure its process_nlu method for specific test cases.
    """
    mock_service = Mock(spec=NLUServiceInterface)
    # Default mock behavior if not overridden by specific test cases
    mock_service.process_nlu.return_value = {"intent": "unknown", "entities": {}}
    return mock_service


@pytest.fixture
def input_processor(mock_nlu_service):
    """Fixture provides an InputProcessor instance."""
    return InputProcessor(nlu_service=mock_nlu_service)


def test_process_text_input_successful_nlu(input_processor, mock_nlu_service):
    """Test input processing where NLU returns a valid intent and entities."""
    test_text = "What's the weather like in New York?"

    # Configure the mock NLU service for this specific test
    mock_nlu_service.process_nlu.return_value = {
        "intent": "get_weather",
        "entities": {"location": "New York"},
    }

    result = input_processor.process_text_input(test_text, TEST_DEVICE_ID)

    # Assertions
    assert result["success"] is True
    assert result["processed_text"] == test_text
    assert result["intent"] == "get_weather"
    assert result["entities"] == {"location": "New York"}
    assert result["user_id"] == TEST_DEVICE_ID
    assert isinstance(result["timestamp"], str)
    assert result["message"] is None
    assert result["error"] is None
    # Verify that the mock NLU service's method was called correctly
    mock_nlu_service.process_nlu.assert_called_once_with(test_text)


def test_process_text_input_unknown_intent(input_processor, mock_nlu_service):
    """Tests text input processing where NLU returns an 'unknown' intent."""
    test_text = "asdfg zxcvb"  # Nonsensical input

    # Configure the mock NLU service to return an unknown intent
    mock_nlu_service.process_nlu.return_value = {
        "intent": "unknown",
        "entities": {"raw_query": test_text},
    }

    result = input_processor.process_text_input(test_text, TEST_DEVICE_ID)

    # Assertions
    assert result["success"] is False
    assert result["processed_text"] == test_text
    assert result["intent"] == "unknown"
    assert result["entities"] == {"raw_query": test_text}
    assert result["user_id"] == TEST_DEVICE_ID
    assert result["message"] is None
    assert result["error"] is None
    mock_nlu_service.process_nlu.assert_called_once_with(test_text)


def test_process_text_input_nlu_processing_error(input_processor, mock_nlu_service):
    """Test input processing when the NLU service on NLUProcessingError."""
    test_text = "This should cause an NLU error."

    # Configure the mock NLU service to raise an NLUProcessingError
    mock_nlu_service.process_nlu.side_effect = NLUProcessingError(
        "API connection failed."
    )

    result = input_processor.process_text_input(test_text, TEST_DEVICE_ID)

    # Assertions
    assert result["success"] is False
    assert result["processed_text"] == test_text
    assert result["intent"] == "unknown"
    assert result["entities"] == {"raw_query": test_text}
    assert "Input processing failed due to NLU" in result["message"]
    assert "API connection failed." in result["error"]
    mock_nlu_service.process_nlu.assert_called_once_with(test_text)


def test_process_text_input_invalid_device_id_format(input_processor, mock_nlu_service):
    """Tests that process_text_input handles an invalid device ID format."""
    test_text = "Hello"
    invalid_device_id = "not-a-uuid"

    result = input_processor.process_text_input(test_text, invalid_device_id)

    assert result["success"] is False
    assert result["processed_text"] == test_text
    assert result["intent"] == "unknown"
    assert result["entities"] == {"raw_query": test_text}
    assert result["user_id"] is None
    assert "Input processing failed due to validation" in result["message"]
    assert "Invalid device_id format" in result["error"]
    mock_nlu_service.process_nlu.assert_not_called()


def test_process_audio_input_basic_flow(input_processor, mock_nlu_service):
    """Test flow of audio input, it calls text processing with simulated ASR."""
    raw_audio_data = b"dummy_audio_bytes"
    simulated_transcription = "What time is it in Tokyo?"

    # Patch the internal _process_nlu call within the InputProcessor when
    # process_text_input is called.
    # We're already mocking nlu_service, so no need to patch _process_nlu
    # directly. The crucial part is that `process_text_input` is called with
    # the *simulated_transcription*.

    # We need to test the logic path of process_audio_input.
    # The `input_processor` fixture already has the `mock_nlu_service`.
    # `process_audio_input` calls `process_text_input`, which then calls
    # `self.nlu_service.process_nlu`.

    # Configure the mock NLU service for this specific test
    mock_nlu_service.process_nlu.return_value = {
        "intent": "get_time",
        "entities": {"location": "Tokyo"},
    }

    result = input_processor.process_audio_input(raw_audio_data, TEST_DEVICE_ID)

    assert result["success"] is True
    assert result["processed_text"] == simulated_transcription
    assert result["intent"] == "get_time"
    assert result["entities"] == {"location": "Tokyo"}
    mock_nlu_service.process_nlu.assert_called_once_with(simulated_transcription)
