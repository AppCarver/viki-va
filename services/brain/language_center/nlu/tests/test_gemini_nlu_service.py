# services/nlu_service/tests/test_gemini_nlu_service.py

"""Unit tests for the GeminiNLUService component."""

import json
import os
from unittest.mock import Mock, patch

import pytest

# Import 'types' to be able to assert against types.GenerateContentConfig
from google.genai import types

from services.brain.language_center.nlu.src.gemini_nlu_service import (
    GeminiNLUService,
)
from services.brain.language_center.nlu.src.nlu_service_interface import (
    NLUServiceInterface,
)


@pytest.fixture
def mock_genai_client():
    """Mock google.genai.Client & models.generate_content method."""
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        # Ensure generate_content is a mock so we can set its return value
        # and check calls
        mock_client.models.generate_content = Mock()
        yield mock_client


@pytest.fixture
def gemini_nlu_service(mock_genai_client):
    """GeminiNLUService instance with a mocked genai client.

    Ensures GOOGLE_API_KEY is set for initialization.
    """
    os.environ["GOOGLE_API_KEY"] = "dummy_api_key_for_test"
    # When initializing GeminiNLUService, it creates its own genai.Client().
    # The fixture mocks genai.Client, so the instance created inside
    # GeminiNLUService will be the mock_client controlled by the fixture.
    service = GeminiNLUService(model_name="gemini-1.5-flash")
    yield service
    del os.environ["GOOGLE_API_KEY"]


def test_gemini_nlu_service_implements_interface():
    """GeminiNLUService correctly implements the NLUServiceInterface."""
    assert issubclass(GeminiNLUService, NLUServiceInterface)


def test_process_nlu_successful(gemini_nlu_service, mock_genai_client):
    """Tests successful NLU processing for a known intent.

    Mocks a valid JSON response from Gemini, including confidence.
    """
    test_text = "What is the weather in Paris?"
    gemini_raw_response = json.dumps(
        {"intent": "get_weather", "entities": {"location": "Paris"}}
    )
    mock_genai_client.models.generate_content.return_value.text = gemini_raw_response

    result = gemini_nlu_service.process_nlu(test_text)

    # Assert generate_content was called with correct prompt and config
    mock_genai_client.models.generate_content.assert_called_once()
    call_kwargs = mock_genai_client.models.generate_content.call_args.kwargs
    # The 'contents' argument is a list, and the first element is the prompt
    # string
    assert f"User Input: {test_text}" in call_kwargs["contents"][0]
    assert isinstance(call_kwargs["config"], types.GenerateContentConfig)
    assert call_kwargs["config"].response_mime_type == "application/json"
    assert call_kwargs["config"].temperature == 0.0

    # Assert the returned NLU result structure, including confidence and
    # original_text
    expected_result = {
        "intent": {"name": "get_weather", "confidence": 0.95},
        "entities": {"location": "Paris"},
        "original_text": test_text,
    }
    assert result == expected_result


def test_process_nlu_unknown_intent(gemini_nlu_service, mock_genai_client):
    """Tests NLU processing for an unknown intent.

    Mocks an "unknown" JSON response from Gemini.
    """
    test_text = "Random gibberish that makes no sense."
    gemini_raw_response = json.dumps(
        {"intent": "unknown", "entities": {"raw_query": test_text}}
    )
    mock_genai_client.models.generate_content.return_value.text = gemini_raw_response

    result = gemini_nlu_service.process_nlu(test_text)

    # Assert generate_content call (same config as above)
    mock_genai_client.models.generate_content.assert_called_once()
    call_kwargs = mock_genai_client.models.generate_content.call_args.kwargs
    assert f"User Input: {test_text}" in call_kwargs["contents"][0]
    assert isinstance(call_kwargs["config"], types.GenerateContentConfig)
    assert call_kwargs["config"].response_mime_type == "application/json"
    assert call_kwargs["config"].temperature == 0.0

    # Assert the returned NLU result structure for unknown intent
    expected_result = {
        "intent": {
            "name": gemini_nlu_service.UNKNOWN_INTENT_NAME,
            "confidence": 0.2,
        },
        "entities": {"raw_query": test_text},
        "original_text": test_text,
    }
    assert result == expected_result


def test_process_nlu_json_decode_error(gemini_nlu_service, mock_genai_client):
    """Tests NLU processing when Gemini returns malformed JSON."""
    test_text = "This response is not JSON"
    # Simulate a non-JSON response that would cause json.loads to fail
    mock_genai_client.models.generate_content.return_value.text = test_text

    result = gemini_nlu_service.process_nlu(test_text)

    # Assert generate_content was called
    mock_genai_client.models.generate_content.assert_called_once()

    # Assert the returned NLU result structure for JSON decode error
    expected_result = {
        "intent": {
            "name": gemini_nlu_service.UNKNOWN_INTENT_NAME,
            "confidence": 0.0,
        },
        "entities": {},
        "original_text": test_text,
    }
    assert result == expected_result


def test_process_nlu_empty_gemini_response(gemini_nlu_service, mock_genai_client):
    """Tests NLU processing when Gemini returns an empty response (None)."""
    from services.input_processor.src.input_processor import NLUProcessingError

    test_text = "Empty response scenario"
    mock_genai_client.models.generate_content.return_value.text = None

    with pytest.raises(NLUProcessingError) as excinfo:
        gemini_nlu_service.process_nlu(test_text)

    # Assert generate_content was called
    mock_genai_client.models.generate_content.assert_called_once()

    assert "Gemini API returned an empty response (None)." in str(excinfo.value)


def test_process_nlu_api_error(gemini_nlu_service, mock_genai_client):
    """Tests NLU processing when Gemini API call itself fails (raises Exception)."""
    from services.input_processor.src.input_processor import NLUProcessingError

    test_text = "API error scenario"
    mock_genai_client.models.generate_content.side_effect = Exception("API call failed")

    with pytest.raises(NLUProcessingError) as excinfo:
        gemini_nlu_service.process_nlu(test_text)

    # Assert generate_content was called
    mock_genai_client.models.generate_content.assert_called_once()

    assert "Gemini API call failed: API call failed" in str(excinfo.value)
