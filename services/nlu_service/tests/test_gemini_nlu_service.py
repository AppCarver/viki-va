# services/nlu_service/tests/test_gemini_nlu_service.py

"""Unit tests for the GeminiNLUService component."""

import json
import os
from unittest.mock import Mock, patch

import pytest

from services.nlu_service.src.gemini_nlu_service import (
    GeminiNLUService,
)
from services.nlu_service.src.nlu_service_interface import NLUServiceInterface


@pytest.fixture
def mock_genai_client():
    """Mock google.genai.Client & models.generate_content method."""
    # FIX: Corrected patch path to reflect 'from google import genai'
    with patch("google.genai.Client") as mock_client_cls:
        # Configure the return_value (the mock instance) and its
        # methods/attributes
        mock_client = mock_client_cls.return_value
        mock_client.models.generate_content.return_value = Mock()
        yield mock_client


@pytest.fixture
def gemini_nlu_service(mock_genai_client):
    """GeminiNLUService instance with a mocked genai client.

    Ensures GOOGLE_API_KEY is set for initialization.
    """
    os.environ["GOOGLE_API_KEY"] = "dummy_api_key_for_test"
    service = GeminiNLUService(mock_genai_client)
    yield service
    del os.environ["GOOGLE_API_KEY"]


def test_gemini_nlu_service_implements_interface():
    """GeminiNLUService correctly implements the NLUServiceInterface."""
    assert issubclass(GeminiNLUService, NLUServiceInterface)


def test_process_nlu_successful(gemini_nlu_service, mock_genai_client):
    """Tests successful NLU processing by GeminiNLUService.

    Mocks a valid JSON response from Gemini.
    """
    test_text = "What is the weather in Paris?"
    expected_response_text = json.dumps(
        {"intent": "get_weather", "entities": {"location": "Paris"}}
    )
    mock_genai_client.models.generate_content.return_value.text = expected_response_text

    result = gemini_nlu_service.process_nlu(test_text)

    # Assert that the generate_content method was called with the expected prompt
    # FIX: Access the prompt string from the 'kwargs' dictionary
    call_kwargs = mock_genai_client.models.generate_content.call_args.kwargs
    # The 'contents' argument is a list, and the first element is the prompt string
    assert f"User Input: {test_text}" in call_kwargs["contents"][0]
    assert result == {"intent": "get_weather", "entities": {"location": "Paris"}}
