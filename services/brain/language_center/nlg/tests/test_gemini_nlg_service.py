# services/brain/language_center/nlg/tests/test_gemini_nlg_service.py

"""Test for the GeminiNLGService functionality."""

import os
from collections.abc import Generator  # Keep this import, it's correct
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest

from services.brain.language_center.nlg.src.gemini_nlg_service import (
    GeminiNLGService,
)
from services.brain.language_center.nlg.src.nlg_service_interface import (
    NLGServiceInterface,
)
from shared_libs.errors.errors import NLGGenerationError


@pytest.fixture
def mock_genai_client() -> Generator[Mock, None, None]:
    """Mock a mock for the Google Generative AI client."""
    with patch("google.genai.Client") as mock_client_cls:
        mock_client_instance = Mock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content = Mock()
        yield mock_client_instance


@pytest.fixture
def gemini_nlg_service(
    mock_genai_client: Mock,
) -> Generator[GeminiNLGService, None, None]:
    """Mock the Gemini NLG service with a mocked GenAI client."""
    os.environ["GOOGLE_API_KEY"] = "dummy_api_key_for_test"
    service = GeminiNLGService(model_name="gemini-pro")
    yield service
    del os.environ["GOOGLE_API_KEY"]


def test_gemini_nlg_service_implements_interface():
    """Verify that GeminiNLGService correctly implements NLGServiceInterface."""
    assert issubclass(GeminiNLGService, NLGServiceInterface)


def test_generate_response_greet(gemini_nlg_service: GeminiNLGService):
    """Test generating a greeting response."""  # D103 Fixed
    mock_generate_content = cast(Any, gemini_nlg_service.client.models.generate_content)
    mock_generate_content.return_value.text = "Hello! How can I help you today?"

    result = gemini_nlg_service.generate_response(
        dialogue_act="greet",
        response_content={},
        conversation_context={},
    )
    assert result["generated_text"] == "Hello! How can I help you today?"
    mock_generate_content.assert_called_once()


def test_generate_response_inform_time(gemini_nlg_service: GeminiNLGService):
    """Test generating a time information response."""  # D103 Fixed
    time_str = "10:30:00 on Thursday, June 12, 2025"
    mock_generate_content = cast(Any, gemini_nlg_service.client.models.generate_content)
    mock_generate_content.return_value.text = f"The time in London is {time_str}"

    result = gemini_nlg_service.generate_response(
        dialogue_act="inform_time",
        response_content={"location": "London", "time": time_str},
        conversation_context={},
    )
    assert result["generated_text"] == f"The time in London is {time_str}"
    mock_generate_content.assert_called_once()


def test_generate_response_tell_joke(gemini_nlg_service: GeminiNLGService):
    """Test generating a joke response."""  # D103 Fixed
    joke_punchline = (
        "Why don't scientists trust atoms? Because they make up everything!"
    )
    mock_generate_content = cast(Any, gemini_nlg_service.client.models.generate_content)
    mock_generate_content.return_value.text = joke_punchline

    result = gemini_nlg_service.generate_response(
        dialogue_act="tell_joke",
        response_content={"joke_punchline": joke_punchline},
        conversation_context={},
    )
    assert result["generated_text"] == joke_punchline
    mock_generate_content.assert_called_once()


def test_generate_response_empty_text_raises_error(
    gemini_nlg_service: GeminiNLGService,
):
    """Test that generate_response raises NLGGenerationError on empty text."""
    mock_generate_content = cast(Any, gemini_nlg_service.client.models.generate_content)
    mock_generate_content.return_value.text = ""  # Simulate empty response

    with pytest.raises(NLGGenerationError) as excinfo:
        gemini_nlg_service.generate_response(
            dialogue_act="greet",
            response_content={},
            conversation_context={},
        )
    assert (
        "Generated response text was empty or consisted only of whitespace after"
        " processing." in str(excinfo.value)
    )
    mock_generate_content.assert_called_once()


def test_generate_response_api_error_raises_error(
    gemini_nlg_service: GeminiNLGService,
):
    """Test that generate_response raises NLGGenerationError on API error."""
    api_error_message = "API Error: Quota exceeded"
    mock_generate_content = cast(Any, gemini_nlg_service.client.models.generate_content)
    mock_generate_content.side_effect = Exception(api_error_message)

    with pytest.raises(NLGGenerationError) as excinfo:
        gemini_nlg_service.generate_response(
            dialogue_act="greet",
            response_content={},
            conversation_context={},
        )
    assert "Gemini API call for NLG failed" in str(excinfo.value)
    mock_generate_content.assert_called_once()


def test_generate_response_ask_for_clarification(
    gemini_nlg_service: GeminiNLGService,
):
    """Test generating a response for 'ask_for_clarification'."""
    mock_generate_content = cast(Any, gemini_nlg_service.client.models.generate_content)
    mock_generate_content.return_value.text = (
        "To help me better understand your request, could you please specify the"
        " location?"
    )
    result = gemini_nlg_service.generate_response(
        dialogue_act="ask_for_clarification",
        response_content={"missing_info": "location"},
        conversation_context={},
    )
    # E501 fixed: Breaking the long string
    expected_text = (
        "To help me better understand your request, could you please specify"
        " the location?"
    )
    assert result["generated_text"] == expected_text
    mock_generate_content.assert_called_once()


def test_generate_response_unimplemented_action(
    gemini_nlg_service: GeminiNLGService,
):
    """Test generating a response for an 'unimplemented_action' intent.

    This tests the fallback mechanism for unimplemented actions.
    """  # D205 Fixed: Blank line added between summary and description
    mock_generate_content = cast(Any, gemini_nlg_service.client.models.generate_content)
    mock_generate_content.return_value.text = "I can't set reminders yet."

    result = gemini_nlg_service.generate_response(
        dialogue_act="unimplemented_action",
        response_content={"intent": "set_reminder"},
        conversation_context={},
    )
    assert result["generated_text"] == "I can't set reminders yet."
    mock_generate_content.assert_called_once()
