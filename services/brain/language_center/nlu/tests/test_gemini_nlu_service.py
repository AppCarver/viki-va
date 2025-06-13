"""Unit tests for the GeminiNLUService component.

This module contains comprehensive unit tests for the `GeminiNLUService`
implementation, focusing on its ability to correctly process Natural
Language Understanding (NLU) requests using the Google Gen AI SDK.

It specifically verifies:
- Proper initialization and adherence to the `NLUServiceInterface`.
- Successful extraction of intent and entities from Gemini API responses,
  including those wrapped in various markdown code block formats (with/without
  'json' tag, and with surrounding conversational text).
- Accurate assignment of confidence scores based on intent recognition.
- Robust error handling for scenarios such as:
    - Empty API responses.
    - Malformed JSON returned by the API (both inside and outside markdown).
    - General API call failures.
- Correct interaction with the `extract_json_from_markdown_code_block`
  utility for robust parsing.
- **Ensuring the `raw_query` entity is present for "unknown" intents,
  even if Gemini omits it.**

Mocks are used for the `google.genai.Client` to simulate API responses
without making actual network calls, ensuring tests are fast and reliable.
"""

import os
from unittest.mock import Mock, patch

import pytest
from google.genai import types

from services.brain.language_center.nlu.src.gemini_nlu_service import (
    GeminiNLUService,
)
from services.brain.language_center.nlu.src.nlu_service_interface import (
    NLUServiceInterface,
)

# Make sure NLUProcessingError is correctly imported (it is in the original)
from services.input_processor.src.input_processor import NLUProcessingError


@pytest.fixture
def mock_genai_client():
    """Mock google.genai.Client & models.generate_content method."""
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.models.generate_content = Mock()
        yield mock_client


@pytest.fixture
def gemini_nlu_service(mock_genai_client):
    """GeminiNLUService instance with a mocked genai client."""
    os.environ["GOOGLE_API_KEY"] = "dummy_api_key_for_test"
    service = GeminiNLUService(model_name="gemini-1.5-flash")
    yield service
    del os.environ["GOOGLE_API_KEY"]


def test_gemini_nlu_service_implements_interface():
    """GeminiNLUService correctly implements the NLUServiceInterface."""
    assert issubclass(GeminiNLUService, NLUServiceInterface)


def test_process_nlu_successful(gemini_nlu_service, mock_genai_client):
    """Tests successful NLU processing for a known intent."""
    test_text = "What is the weather in Paris?"
    # Simulate Gemini response with markdown and 'json' tag
    gemini_raw_response = (
        '```json\n{"intent": "get_weather", "entities": {"location": "Paris"}}\n```'
    )
    mock_genai_client.models.generate_content.return_value.text = gemini_raw_response

    result = gemini_nlu_service.process_nlu(test_text)

    mock_genai_client.models.generate_content.assert_called_once()
    call_kwargs = mock_genai_client.models.generate_content.call_args.kwargs
    assert f"User Input: {test_text}" in call_kwargs["contents"][0]
    assert isinstance(call_kwargs["config"], types.GenerateContentConfig)
    assert call_kwargs["config"].response_mime_type == "application/json"
    assert call_kwargs["config"].temperature == 0.0

    expected_result = {
        "intent": {"name": "get_weather", "confidence": 0.95},
        "entities": {"location": "Paris"},
        "original_text": test_text,
    }
    assert result == expected_result


def test_process_nlu_unknown_intent(gemini_nlu_service, mock_genai_client):
    """Tests NLU processing for an unknown intent, including markdown wrapper.

    Gemini is mocked to provide raw_query in this case.
    """
    test_text = "Random gibberish that makes no sense."
    # Simulate Gemini response with markdown and 'json' tag for unknown intent
    gemini_raw_response = (
        f'```json\n{{"intent": "unknown", '
        f'"entities": {{"raw_query": "{test_text}"}}}}\n```'
    )
    mock_genai_client.models.generate_content.return_value.text = gemini_raw_response

    result = gemini_nlu_service.process_nlu(test_text)

    mock_genai_client.models.generate_content.assert_called_once()
    call_kwargs = mock_genai_client.models.generate_content.call_args.kwargs
    assert f"User Input: {test_text}" in call_kwargs["contents"][0]
    assert isinstance(call_kwargs["config"], types.GenerateContentConfig)
    assert call_kwargs["config"].response_mime_type == "application/json"
    assert call_kwargs["config"].temperature == 0.0

    expected_result = {
        "intent": {
            "name": gemini_nlu_service.UNKNOWN_INTENT_NAME,
            "confidence": 0.2,
        },
        "entities": {"raw_query": test_text},
        "original_text": test_text,
    }
    assert result == expected_result


# --- NEW TEST CASE FOR ACCEPTANCE CRITERIA ---
def test_process_nlu_adds_raw_query_for_unknown_intent_if_gemini_omits(
    gemini_nlu_service, mock_genai_client
):
    """Test process_nlu adds raw_query if Gemini returns unknown intent without it."""
    test_text = "What is this random query about?"
    # Simulate Gemini response with unknown intent but MISSING raw_query entity
    gemini_raw_response = '```json\n{"intent": "unknown", "entities": {}}\n```'
    mock_genai_client.models.generate_content.return_value.text = gemini_raw_response

    result = gemini_nlu_service.process_nlu(test_text)

    mock_genai_client.models.generate_content.assert_called_once()

    expected_result = {
        "intent": {
            "name": gemini_nlu_service.UNKNOWN_INTENT_NAME,
            "confidence": 0.2,
        },
        "entities": {"raw_query": test_text},  # Assert that raw_query was added
        "original_text": test_text,
    }
    assert result == expected_result


# --- END NEW TEST CASE ---


def test_process_nlu_no_json_tag_in_markdown(gemini_nlu_service, mock_genai_client):
    """Tests NLU with markdown fences but no 'json' tag."""
    test_text = "Turn off the lights."
    gemini_raw_response = (
        '```\n{"intent": "turn_off", "entities": {"device": "lights"}}\n```'
    )
    mock_genai_client.models.generate_content.return_value.text = gemini_raw_response

    result = gemini_nlu_service.process_nlu(test_text)
    expected_result = {
        "intent": {"name": "turn_off", "confidence": 0.95},
        "entities": {"device": "lights"},
        "original_text": test_text,
    }
    assert result == expected_result


def test_process_nlu_json_with_surrounding_text(gemini_nlu_service, mock_genai_client):
    """Tests NLU with markdown JSON block embedded in conversational text."""
    test_text = "Hey Viki, can you please set a timer for 10 minutes? Thanks!"
    gemini_raw_response = (
        "Okay, here is the JSON for that: ```json\n"
        '{"intent": "set_timer", "entities": {"duration": "10 minutes"}}\n'
        "``` Let me know if you need anything else."
    )
    mock_genai_client.models.generate_content.return_value.text = gemini_raw_response

    result = gemini_nlu_service.process_nlu(test_text)
    expected_result = {
        "intent": {"name": "set_timer", "confidence": 0.95},
        "entities": {"duration": "10 minutes"},
        "original_text": test_text,
    }
    assert result == expected_result


def test_process_nlu_malformed_json_in_markdown_block(
    gemini_nlu_service, mock_genai_client
):
    """Tests NLU when Gemini returns malformed JSON within a markdown block.

    Should now include raw_query in entities for unknown intent.
    """
    test_text = "Malformed JSON test"
    # The markdown fences are present, but the JSON itself is invalid inside
    gemini_raw_response = (
        '```json\n{"intent": "malformed", "entities": {"location": "Paris"```\n```'
    )
    mock_genai_client.models.generate_content.return_value.text = gemini_raw_response

    result = gemini_nlu_service.process_nlu(test_text)

    # Assert that it returns the unknown intent with 0.0 confidence,
    # and now includes raw_query as the parser failed to extract valid JSON.
    expected_result = {
        "intent": {
            "name": gemini_nlu_service.UNKNOWN_INTENT_NAME,
            "confidence": 0.0,
        },
        "entities": {"raw_query": test_text},  # MODIFIED: raw_query added here
        "original_text": test_text,
    }
    assert result == expected_result


# The following tests (json_decode_error, empty_gemini_response, api_error)
# should still work as before since their core behavior is to test error paths
# that occur before or after the response_parser is successfully used.
# The `json_decode_error` test's input "This response is not JSON" will
# correctly cause `extract_json_from_markdown_code_block` to return `None`,
# leading to the expected 0.0 confidence unknown intent.


def test_process_nlu_json_decode_error(gemini_nlu_service, mock_genai_client):
    """Tests NLU processing when Gemini returns malformed JSON (not in markdown).

    Should now include raw_query in entities for unknown intent.
    """
    test_text = "This response is not JSON"
    mock_genai_client.models.generate_content.return_value.text = test_text

    result = gemini_nlu_service.process_nlu(test_text)

    mock_genai_client.models.generate_content.assert_called_once()

    expected_result = {
        "intent": {
            "name": gemini_nlu_service.UNKNOWN_INTENT_NAME,
            "confidence": 0.0,
        },
        "entities": {"raw_query": test_text},  # MODIFIED: raw_query added here
        "original_text": test_text,
    }
    assert result == expected_result


def test_process_nlu_empty_gemini_response(gemini_nlu_service, mock_genai_client):
    """Tests NLU processing when Gemini returns an empty response (None)."""
    test_text = "Empty response scenario"
    mock_genai_client.models.generate_content.return_value.text = None

    with pytest.raises(NLUProcessingError) as excinfo:
        gemini_nlu_service.process_nlu(test_text)

    mock_genai_client.models.generate_content.assert_called_once()

    assert "Gemini API returned an empty response (None)." in str(excinfo.value)


def test_process_nlu_api_error(gemini_nlu_service, mock_genai_client):
    """Tests NLU processing when Gemini API call itself fails (raises Exception)."""
    test_text = "API error scenario"
    mock_genai_client.models.generate_content.side_effect = Exception("API call failed")

    with pytest.raises(NLUProcessingError) as excinfo:
        gemini_nlu_service.process_nlu(test_text)

    mock_genai_client.models.generate_content.assert_called_once()

    assert "Gemini API call failed: API call failed" in str(excinfo.value)
