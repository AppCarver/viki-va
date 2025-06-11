# tests/test_dummy.py

"""A dummy test module to ensure pytest and linters pass."""

# Imports

from datetime import datetime
from unittest.mock import patch  # <--- Ensure Mock and patch are here!

import pytest
import pytz

from services.action_executor.src.action_executor import ActionExecutor


# Test Fixtures
@pytest.fixture
def action_executor():
    """Fixture provides an ActionExecutor instance."""
    return ActionExecutor()


# Test Cases


# Scenario: Provide a well-formed intent and a dictionary of entities that the
# ActionExecutor should know how to handle
# (e.g., intent="greet", entities={}).
def test_greet_success(action_executor):
    """Test ActionExecutor for greeting response."""
    result = action_executor.execute_action(intent="greet", entities={})

    assert result == "Hello there! How can I help you today?"


def test_tell_joke_success(action_executor):
    """Test ActionExecutor for telling a joke."""
    result = action_executor.execute_action(intent="tell_joke", entities={})

    assert result == (
        "Why don't scientists trust atoms? Because they make up everything!"
    )


def test_get_time_for_specific_location(action_executor):
    """Test getting specific time."""
    # 1. Arrange - Define a fixed time for our mock
    fixed_utc_time = datetime(2023, 1, 15, 10, 30, 0, tzinfo=pytz.utc)

    # 2. Arrange - Define intent and entities
    intent = "get_time"
    location = "Paris"
    entities = {"location": location}

    # 3. Arrange - Calculate the expected response string
    expected_timezone = pytz.timezone("Europe/Paris")
    expected_local_time = fixed_utc_time.astimezone(expected_timezone)
    expected_time_str = expected_local_time.strftime("%H:%M:%S on %A, %B %d, %Y")
    expected_response = f"The current time in {location} is {expected_time_str}."

    # 4. Act - Use patch to "freeze" datetime.datetime.now()
    # We patch the 'datetime' *module* as it's imported in action_executor.py
    # and then configure its 'now' method to return our fixed time.
    with patch(
        "services.action_executor.src.action_executor.datetime"
    ) as mock_datetime:
        # Configure the mock datetime module's 'now' method
        mock_datetime.now.return_value = fixed_utc_time

        result = action_executor.execute_action(intent=intent, entities=entities)

    # 5. Assert
    assert result == expected_response


def test_get_time_for_missing_location(action_executor):
    """Test getting specific time."""
    # 1. Arrange - Define a fixed time for our mock
    fixed_utc_time = datetime(2023, 1, 15, 10, 30, 0, tzinfo=pytz.utc)

    # 2. Arrange - Define intent and entities
    intent = "get_time"
    location = ""
    entities = {"location": location}

    # 3. Arrange - Calculate the expected response string
    expected_time_str = fixed_utc_time.strftime("%H:%M:%S")
    expected_response = (
        f"You asked for the time, but didn't specify a location. "
        f"The current UTC time is {expected_time_str}."
    )

    # 4. Act - Use patch to "freeze" datetime.datetime.now()
    # We patch the 'datetime' *module* as it's imported in action_executor.py
    # and then configure its 'now' method to return our fixed time.
    with patch(
        "services.action_executor.src.action_executor.datetime"
    ) as mock_datetime:
        # Configure the mock datetime module's 'now' method
        mock_datetime.now.return_value = fixed_utc_time

        result = action_executor.execute_action(intent=intent, entities=entities)

    # 5. Assert
    assert result == expected_response


def test_unrecognized_intent(action_executor):
    """Test ActionExecutor for unrecognized intent."""
    intent = "do_a_backflip"

    result = action_executor.execute_action(intent=intent, entities={})

    assert result == (
        f"I understand you want to '{intent}', but I don't have an action for that yet."
    )


def test_get_time_unknown_timezone_error(action_executor):
    """Test unknown timezone."""
    # 1. Arrange - Define a fixed time for our mock
    fixed_utc_time = datetime(2023, 1, 15, 10, 30, 0, tzinfo=pytz.utc)

    # 2. Arrange - Define intent and entities
    intent = "get_time"
    location = "Cancun"
    entities = {"location": location}

    expected_response = (
        f"I'm not sure about the timezone for '{location}'. Can you be more specific?"
    )

    # 4. Act - Use patch to "freeze" datetime.datetime.now()
    # We patch the 'datetime' *module* as it's imported in action_executor.py
    # and then configure its 'now' method to return our fixed time.
    with patch(
        "services.action_executor.src.action_executor.datetime"
    ) as mock_datetime:
        # Configure the mock datetime module's 'now' method
        mock_datetime.now.return_value = fixed_utc_time

        result = action_executor.execute_action(intent=intent, entities=entities)

    # 5. Assert
    assert result == expected_response


def test_get_time_pytz_unknown_timezone_exception(action_executor):
    """Test get_time when pytz.timezone raises UnknownTimeZoneError."""
    # Arrange
    intent = "get_time"

    location = "London"  # Or any other mapped city like "Paris", "New York"
    entities = {"location": location}

    expected_response = (
        f"I don't recognize the timezone for '{location}'. Please try a different city."
    )

    # Act
    # We need to patch pytz.timezone within the context of the action_executor module.
    # Also, keep the datetime mock consistent to avoid other side effects.
    with patch(
        "services.action_executor.src.action_executor.pytz.timezone"
    ) as mock_pytz_timezone:
        mock_pytz_timezone.side_effect = pytz.exceptions.UnknownTimeZoneError

        result = action_executor.execute_action(intent=intent, entities=entities)

    # Assert
    assert result == expected_response
    # You could also assert that mock_pytz_timezone was called with the correct string
    mock_pytz_timezone.assert_called_once_with("Europe/London")
    # Verify it was called with the actual timezone string


def test_get_time_general_exception_in_location_helper(action_executor):
    """Test get_time when pytz.timezone raises UnknownTimeZoneError."""
    # Arrange
    intent = "get_time"
    location = "London"  # Or any other mapped city like "Paris", "New York"
    entities = {"location": location}

    expected_response = (
        "I encountered an error trying to get the time for that location."
    )

    with patch(
        "services.action_executor.src.action_executor.pytz.timezone"
    ) as mock_pytz_timezone:
        mock_pytz_timezone.side_effect = pytz.exceptions.Error
        result = action_executor.execute_action(intent=intent, entities=entities)

    # Assert
    assert result == expected_response
    mock_pytz_timezone.assert_called_once_with("Europe/London")
