# services/action_executor/tests/test_action_executor.py

"""Tests for the ActionExecutor service."""

from collections.abc import Generator
from datetime import datetime
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest
import pytz

from services.action_executor.src.action_executor import ActionExecutor


@pytest.fixture
def action_executor() -> Generator[ActionExecutor, None, None]:
    """Provide a clean ActionExecutor instance for each test."""
    yield ActionExecutor()


# --- New Tests for get_name intent ---
def test_get_name_success(action_executor: ActionExecutor):
    """Test 'get_name' intent successfully returns Viki's name."""
    intent = "get_name"
    entities: dict[str, Any] = {}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )
    assert response["success"] is True
    assert response["error"] is None
    assert response["result_data"]["dialogue_act"] == "inform_name"
    assert response["result_data"]["viki_name"] == "Viki"
    assert response["result_data"]["message"] == "My name is Viki."


# --- Tests for existing intents with updated assertions for new structure ---
def test_greet_success(action_executor: ActionExecutor):
    """Test 'greet' intent with a user name."""
    intent = "greet"
    entities = {"user_name": "Alice"}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )
    assert response["success"] is True
    assert response["error"] is None
    assert response["result_data"]["dialogue_act"] == "greet"
    assert response["result_data"]["user_name"] == "Alice"
    assert response["result_data"]["message"] == "Hello Alice!"


def test_greet_no_name(action_executor: ActionExecutor):
    """Test 'greet' intent without a user name."""
    intent = "greet"
    entities: dict[str, Any] = {}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )
    assert response["success"] is True
    assert response["error"] is None
    assert response["result_data"]["dialogue_act"] == "greet"
    assert response["result_data"]["user_name"] is None
    assert response["result_data"]["message"] == "Hello!"


def test_tell_joke_success(action_executor: ActionExecutor):
    """Test 'tell_joke' intent."""
    intent = "tell_joke"
    entities: dict[str, Any] = {}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )
    assert response["success"] is True
    assert response["error"] is None
    assert response["result_data"]["dialogue_act"] == "tell_joke"
    assert (
        response["result_data"]["joke_punchline"]
        == "Why don't scientists trust atoms? Because they make up everything!"
    )
    assert (
        response["result_data"]["message"]
        == "Why don't scientists trust atoms? Because they make up everything!"
    )


@patch("services.action_executor.src.action_executor.datetime")
def test_get_time_for_specific_location(
    mock_datetime: MagicMock, action_executor: ActionExecutor
):
    """Test 'get_time' intent with a specific location."""
    fixed_utc_time = datetime(2025, 6, 11, 10, 0, 0, tzinfo=pytz.utc)
    # Cast mock_datetime.now to Any to satisfy mypy for .return_value
    cast(Any, mock_datetime.now).return_value = fixed_utc_time

    intent = "get_time"
    entities = {"location": "London"}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )

    assert response["success"] is True
    assert response["error"] is None
    assert response["result_data"]["dialogue_act"] == "inform_time"
    assert response["result_data"]["location"] == "London"
    assert response["result_data"]["time"] == ("11:00:00 on Wednesday, June 11, 2025")
    assert response["result_data"]["message"] == (
        "The current time in London is 11:00:00 on Wednesday, June 11, 2025."
    )


@patch("services.action_executor.src.action_executor.datetime")
def test_get_time_for_missing_location(
    mock_datetime: MagicMock, action_executor: ActionExecutor
):
    """Test 'get_time' intent when location is missing (asks for clarification)."""
    fixed_utc_time = datetime(2025, 6, 11, 10, 0, 0, tzinfo=pytz.utc)
    # Cast mock_datetime.now to Any to satisfy mypy for .return_value
    cast(Any, mock_datetime.now).return_value = fixed_utc_time

    intent = "get_time"
    entities: dict[str, Any] = {}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )

    assert response["success"] is False
    assert response["result_data"] is None
    assert response["error"]["code"] == "MISSING_PARAMETER"
    assert response["error"]["message"] == "Please specify a location to get the time."
    assert (
        response["error"]["details"]
        == "Missing 'location' entity for 'get_time' intent. Current UTC: 10:00:00 UTC"
    )


def test_unimplemented_intent(action_executor: ActionExecutor):
    """Test an intent that is understood but not yet implemented."""
    intent = "set_reminder"
    entities = {"item": "groceries"}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )
    assert response["success"] is False
    assert response["result_data"] is None
    assert response["error"]["code"] == "UNIMPLEMENTED_ACTION"
    assert (
        response["error"]["message"]
        == "I know the intent 'set_reminder', but I don't have a specific action "
        "implemented for it yet."
    )
    assert response["error"]["details"] == (
        "Intent: set_reminder, Entities: {'item': 'groceries'}"
    )


def test_unknown_intent(action_executor: ActionExecutor):
    """Test an unknown intent."""
    intent = "unknown"
    entities = {"raw_query": "random gibberish"}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )
    assert response["success"] is False
    assert response["result_data"] is None
    assert response["error"]["code"] == "UNKNOWN_INTENT"
    assert response["error"]["message"] == "I'm sorry, I don't understand that request."
    assert (
        response["error"]["details"]
        == "Received unknown intent. Raw query: 'random gibberish'"
    )


def test_farewell_intent(action_executor: ActionExecutor):
    """Test the 'farewell' intent."""
    intent = "farewell"
    entities: dict[str, Any] = {}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )
    assert response["success"] is True
    assert response["error"] is None
    assert response["result_data"]["dialogue_act"] == "farewell"
    assert response["result_data"]["message"] == "Goodbye! It was nice talking to you."


@patch("services.action_executor.src.action_executor.pytz.timezone")
def test_get_time_unknown_timezone_error(
    mock_timezone: MagicMock, action_executor: ActionExecutor
):
    """Test _get_time_for_location with an unknown timezone."""
    cast(Any, mock_timezone).side_effect = pytz.exceptions.UnknownTimeZoneError(
        "Unknown/Location"
    )
    intent = "get_time"
    entities = {"location": "Unknown/Location"}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )
    assert response["success"] is False
    assert response["result_data"] is None
    assert response["error"]["code"] == "TIME_ERROR"
    assert response["error"]["message"] == (
        "I'm not sure about the timezone for 'Unknown/Location'. Can you be more "
        "specific?"
    )
    assert "Failed to get time for Unknown/Location" in response["error"]["details"]


@patch("services.action_executor.src.action_executor.pytz.timezone")
def test_get_time_general_exception_in_location_helper(
    mock_timezone: MagicMock, action_executor: ActionExecutor
):
    """Test _get_time_for_location with a general exception."""
    cast(Any, mock_timezone).side_effect = Exception("Some unexpected error")
    intent = "get_time"
    entities = {"location": "Anywhere"}
    response = action_executor.execute_action_and_get_structured_response(
        intent, entities
    )
    assert response["success"] is False
    assert response["result_data"] is None
    assert response["error"]["code"] == "TIME_ERROR"
    assert response["error"]["message"] == (
        "I'm not sure about the timezone for 'Anywhere'. Can you be more specific?"
    )
    assert "Failed to get time for Anywhere" in response["error"]["details"]


# --- New Tests for intent name parsing robustness ---
def test_execute_action_with_dict_intent_format(action_executor: ActionExecutor):
    """Test handling of intent as a dictionary from NLU."""
    intent_dict = {"name": "get_name", "confidence": 0.98}
    entities: dict[str, Any] = {}
    response = action_executor.execute_action_and_get_structured_response(
        intent_dict, entities
    )
    assert response["success"] is True
    assert response["result_data"]["dialogue_act"] == "inform_name"


def test_execute_action_with_invalid_intent_format(action_executor: ActionExecutor):
    """Test handling of an unparseable intent format."""
    intent_list = ["get_name", 0.98]  # Invalid format
    entities: dict[str, Any] = {}
    response = action_executor.execute_action_and_get_structured_response(
        intent_list, entities
    )
    assert response["success"] is False
    assert response["result_data"] is None
    assert response["error"]["code"] == "INVALID_INTENT_FORMAT"
    assert (
        response["error"]["message"]
        == "ActionExecutor received an unparseable intent format."
    )
    assert "Intent: ['get_name', 0.98]" in response["error"]["details"]
