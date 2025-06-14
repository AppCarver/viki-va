"""Tests the pre-frontalcortex module."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from services.brain.pre_forntal_cortex.src.pre_frontal_cortex import (
    PrefrontalCortex,
)
from services.brain.short_term_mem.src.short_term_memory import (
    ShortTermMemory,
)


@pytest.fixture
def prefrontal_cortex_instance() -> PrefrontalCortex:
    """Provide a fresh PrefrontalCortex instance for each test."""
    # The PrefrontalCortex's __init__ will create a ShortTermMemory instance.
    # We will patch that ShortTermMemory instance in specific tests.
    return PrefrontalCortex()


@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ShortTermMemory")
def test_prefrontal_cortex_initializes_short_term_memory(
    mock_short_term_memory_class: MagicMock,
):
    """Test that PrefrontalCortex initializes ShortTermMemory on startup."""
    pfc = PrefrontalCortex()
    # Verify that ShortTermMemory's constructor was called
    mock_short_term_memory_class.assert_called_once()
    # Verify the instance is stored
    assert isinstance(pfc.short_term_memory, MagicMock)


@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ShortTermMemory")
def test_process_dialogue_turn_loads_and_updates_context(
    mock_short_term_memory_class: MagicMock,
):
    """Test that process_dialogue_turn loads existing context and updates it."""
    # Setup mock ShortTermMemory instance
    mock_short_term_memory_instance = MagicMock(spec=ShortTermMemory)
    # Configure get_conversation_context to return an existing context
    mock_short_term_memory_instance.get_conversation_context.return_value = {
        "user_id": str(uuid4()),
        "interaction_count": 5,
        "existing_data": "value",
    }
    # Link the mock class to return our mock instance
    mock_short_term_memory_class.return_value = mock_short_term_memory_instance

    pfc = PrefrontalCortex()

    conversation_id = uuid4()
    user_id = uuid4()
    turn_id = uuid4()
    processed_text = "test user input"
    nlu_results = {"intent": "test_intent", "entities": {}}

    # Call the method under test
    response = pfc.process_dialogue_turn(
        turn_id, conversation_id, user_id, processed_text, nlu_results
    )

    # Assertions for ShortTermMemory interactions
    mock_short_term_memory_instance.get_conversation_context.assert_called_once_with(
        conversation_id
    )
    mock_short_term_memory_instance.update_conversation_context.assert_called_once()

    # Get the arguments passed to update_conversation_context
    args, kwargs = mock_short_term_memory_instance.update_conversation_context.call_args
    updated_conv_id = args[0]
    updated_context = args[1]

    assert updated_conv_id == conversation_id
    assert updated_context["last_turn_id"] == str(turn_id)
    assert updated_context["last_processed_text"] == processed_text
    assert updated_context["last_nlu_results"] == nlu_results
    assert updated_context["interaction_count"] == 6  # Incremented from 5
    assert updated_context["user_id"] == str(user_id)
    assert updated_context["existing_data"] == "value"  # Ensure existing data persists
    assert "last_active_timestamp" in updated_context

    # Assertions for PrefrontalCortex's own return value
    assert response["success"] is True
    assert "PrefrontalCortex processed your input" in response["va_response_text"]
    assert response["action_taken"] == "context_updated"


@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ShortTermMemory")
def test_process_dialogue_turn_creates_new_context(
    mock_short_term_memory_class: MagicMock,
):
    """Test that process_dialogue_turn creates a new context if none exists."""
    mock_short_term_memory_instance = MagicMock(spec=ShortTermMemory)
    # Configure get_conversation_context to return None (no existing context)
    mock_short_term_memory_instance.get_conversation_context.return_value = None
    mock_short_term_memory_class.return_value = mock_short_term_memory_instance

    pfc = PrefrontalCortex()

    conversation_id = uuid4()
    user_id = uuid4()
    turn_id = uuid4()
    processed_text = "first user input"
    nlu_results = {"intent": "initial_greet", "entities": {}}

    response = pfc.process_dialogue_turn(
        turn_id, conversation_id, user_id, processed_text, nlu_results
    )

    mock_short_term_memory_instance.get_conversation_context.assert_called_once_with(
        conversation_id
    )
    mock_short_term_memory_instance.update_conversation_context.assert_called_once()

    args, kwargs = mock_short_term_memory_instance.update_conversation_context.call_args
    updated_conv_id = args[0]
    updated_context = args[1]

    assert updated_conv_id == conversation_id
    assert updated_context["last_turn_id"] == str(turn_id)
    assert updated_context["last_processed_text"] == processed_text
    assert updated_context["last_nlu_results"] == nlu_results
    assert updated_context["interaction_count"] == 1  # Should be 1 for new context
    assert updated_context["user_id"] == str(user_id)
    assert "last_active_timestamp" in updated_context

    assert response["success"] is True
