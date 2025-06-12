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


def test_greet_success(action_executor: ActionExecutor):
    """Test 'greet' intent with a user name."""
    intent = "greet"
    entities = {"user_name": "Alice"}
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )
    assert dialogue_act == "greet"
    assert response_content == {"user_name": "Alice"}


def test_greet_no_name(action_executor: ActionExecutor):
    """Test 'greet' intent without a user name."""
    intent = "greet"
    entities: dict[str, Any] = {}
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )
    assert dialogue_act == "greet"
    assert response_content == {}


def test_tell_joke_success(action_executor: ActionExecutor):
    """Test 'tell_joke' intent."""
    intent = "tell_joke"
    entities: dict[str, Any] = {}
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )
    assert dialogue_act == "tell_joke"
    assert "joke_punchline" in response_content
    assert (
        response_content["joke_punchline"]
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
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )

    assert dialogue_act == "inform_time"
    assert response_content["location"] == "London"
    # London (Europe/London) is UTC+1 (BST) on June 11th. So 10 AM UTC becomes
    # 11 AM London. # E501 fixed by splitting the comment
    # Format from ActionExecutor is "%H:%M:%S on %A, %B %d, %Y"
    assert response_content["time"] == "11:00:00 on Wednesday, June 11, 2025"


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
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )

    assert dialogue_act == "ask_for_clarification"
    assert response_content["missing_info"] == "location for time"
    assert response_content["current_utc_time"] == "10:00:00 UTC"


def test_unimplemented_intent(action_executor: ActionExecutor):
    """Test an intent that is understood but not yet implemented."""
    intent = "set_reminder"
    entities = {"item": "groceries"}
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )
    assert dialogue_act == "unimplemented_action"
    assert response_content == {"intent": "set_reminder"}


def test_unknown_intent(action_executor: ActionExecutor):
    """Test an unknown intent."""
    intent = "unknown"
    entities = {"raw_query": "random gibberish"}
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )
    assert dialogue_act == "unknown_intent_response"
    assert response_content == {"raw_query": "random gibberish"}


def test_farewell_intent(action_executor: ActionExecutor):
    """Test the 'farewell' intent."""
    intent = "farewell"
    entities: dict[str, Any] = {}
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )
    assert dialogue_act == "farewell"
    assert response_content == {}


@patch("services.action_executor.src.action_executor.pytz.timezone")
def test_get_time_unknown_timezone_error(
    mock_timezone: MagicMock, action_executor: ActionExecutor
):
    """Test _get_time_for_location with an unknown timezone.

    This specifically tests the handling of pytz.UnknownTimeZoneError.
    """
    # Cast mock_timezone to Any to satisfy mypy for .side_effect
    cast(Any, mock_timezone).side_effect = pytz.exceptions.UnknownTimeZoneError(
        "Unknown/Location"
    )
    intent = "get_time"
    entities = {"location": "Unknown/Location"}
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )
    assert dialogue_act == "inform_error"
    assert response_content["error_message"] == (
        "I'm not sure about the timezone for 'Unknown/Location'. Can you be more"
        " specific?"
    )


@patch("services.action_executor.src.action_executor.pytz.timezone")
def test_get_time_general_exception_in_location_helper(
    mock_timezone: MagicMock, action_executor: ActionExecutor
):
    """Test _get_time_for_location with a general exception.

    This tests error handling for unexpected issues during timezone lookup.
    """
    # Cast mock_timezone to Any to satisfy mypy for .side_effect
    cast(Any, mock_timezone).side_effect = Exception("Some unexpected error")
    intent = "get_time"
    entities = {"location": "Anywhere"}
    dialogue_act, response_content = (
        action_executor.execute_action_and_get_structured_response(intent, entities)
    )
    assert dialogue_act == "inform_error"
    assert response_content["error_message"] == (
        "I'm not sure about the timezone for 'Anywhere'. Can you be more specific?"
    )
