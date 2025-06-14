"""Test Pre-Frontalcortex module."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from services.action_executor.src.action_executor import ActionExecutor
from services.brain.pre_forntal_cortex.src.pre_frontal_cortex import (
    PrefrontalCortex,
)
from services.brain.short_term_mem.src.short_term_memory import (
    ShortTermMemory,
)


@pytest.fixture
def prefrontal_cortex_instance() -> PrefrontalCortex:
    """Provide a PrefrontalCortex instance for each test, with mocked depend.."""
    # Create mocks for the required dependencies
    mock_short_term_memory = MagicMock(spec=ShortTermMemory)
    mock_action_executor = MagicMock(spec=ActionExecutor)

    # Return a PrefrontalCortex instance initialized with the mocks
    return PrefrontalCortex(
        short_term_memory=mock_short_term_memory, action_executor=mock_action_executor
    )


# --- CRITICAL MODIFICATION FOR THIS TEST ---
# This test verifies that dependencies are *stored*, not *instantiated* by PFC.
# Therefore, it should NOT use @patch decorators for the dependencies it receives.
# Remove the @patch decorators from this test function.
# Rename the function to be more accurate.
def test_prefrontal_cortex_stores_dependencies():
    """Test that PrefrontalCortex correctly stores its provided dependencies."""
    mock_short_term_memory = MagicMock(spec=ShortTermMemory)
    mock_action_executor = MagicMock(spec=ActionExecutor)

    pfc = PrefrontalCortex(
        short_term_memory=mock_short_term_memory,
        action_executor=mock_action_executor,
    )

    # Verify that the provided mock instances are stored correctly
    assert pfc.short_term_memory == mock_short_term_memory
    assert pfc.action_executor == mock_action_executor

    # REMOVED: mock_short_term_memory_class.assert_called_once()
    # REMOVED: mock_action_executor_class.assert_called_once()
    # These assertions are incorrect for dependency injection.


# --- END CRITICAL MODIFICATION ---


# @patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ShortTermMemory")
# @patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ActionExecutor")
# def test_prefrontal_cortex_initializes_short_term_memory(
#    mock_action_executor_class: MagicMock,  # <-- Order matters for patched arguments
#    mock_short_term_memory_class: MagicMock,
# ):
#    """Test that PrefrontalCortex initializes ShortTermMemory on startup."""
#    pfc = PrefrontalCortex(
#        short_term_memory=mock_short_term_memory_class.return_value,
#        action_executor=mock_action_executor_class.return_value,
#    )
#    # Verify that ShortTermMemory's constructor was called
#    mock_short_term_memory_class.assert_called_once()
#    mock_action_executor_class.assert_called_once()
#    # Verify the instances are stored
#    assert isinstance(pfc.short_term_memory, MagicMock)
#    assert isinstance(pfc.action_executor, MagicMock)


@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ShortTermMemory")
@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ActionExecutor")
def test_process_dialogue_turn_loads_and_updates_context(
    mock_action_executor_class: MagicMock,
    mock_short_term_memory_class: MagicMock,
):
    """Test that process_dialogue_turn loads existing context and updates it."""
    # Setup mock ShortTermMemory instance (this will be the instance
    # returned by mock_short_term_memory_class)
    mock_short_term_memory_instance = MagicMock(spec=ShortTermMemory)
    # Configure get_conversation_context to return an existing context
    mock_short_term_memory_instance.get_conversation_context.return_value = {
        "user_id": str(uuid4()),
        "interaction_count": 5,
        "dialogue_state": "IDLE",  # Add initial dialogue state
        "existing_data": "value",
    }
    # Link the mock class to return our mock instance
    mock_short_term_memory_class.return_value = mock_short_term_memory_instance

    pfc = PrefrontalCortex(
        short_term_memory=mock_short_term_memory_instance,
        action_executor=mock_action_executor_class.return_value,
    )

    conversation_id = uuid4()
    user_id = uuid4()
    turn_id = uuid4()
    processed_text = "test user input"
    nlu_results = {
        "intent": {"name": "greet", "confidence": 0.95},
        "entities": {},
    }  # Example NLU results

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
    assert updated_context["dialogue_state"] == "GREETING_INITIATED"

    # Assertions for PrefrontalCortex's own return value
    assert response["success"] is True
    assert "Hello! How can I help you today?" in response["va_response_text"]
    assert response["action_taken"] is None  # No action_executor call yet in PFC logic
    assert response["new_dialogue_state"] == "GREETING_INITIATED"


@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ShortTermMemory")
@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ActionExecutor")
def test_process_dialogue_turn_creates_new_context(
    mock_action_executor_class: MagicMock,
    mock_short_term_memory_class: MagicMock,
):
    """Test that process_dialogue_turn creates a new context if none exists."""
    mock_short_term_memory_instance = MagicMock(spec=ShortTermMemory)
    # Configure get_conversation_context to return None (no existing context)
    mock_short_term_memory_instance.get_conversation_context.return_value = None
    mock_short_term_memory_class.return_value = mock_short_term_memory_instance

    # MODIFIED: Instantiate PrefrontalCortex with the mocked dependencies
    pfc = PrefrontalCortex(
        short_term_memory=mock_short_term_memory_instance,
        action_executor=mock_action_executor_class.return_value,
    )

    conversation_id = uuid4()
    user_id = uuid4()
    turn_id = uuid4()
    processed_text = "first user input"
    nlu_results = {
        "intent": {"name": "greet", "confidence": 0.98},
        "entities": {},
    }

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
    assert updated_context["interaction_count"] == 1
    assert updated_context["user_id"] == str(user_id)
    assert "last_active_timestamp" in updated_context
    assert updated_context["dialogue_state"] == "GREETING_INITIATED"

    assert response["success"] is True
    assert "Hello! How can I help you today?" in response["va_response_text"]
    assert response["action_taken"] is None
    assert response["new_dialogue_state"] == "GREETING_INITIATED"


# --- New tests for dialogue policy logic ---


@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ShortTermMemory")
@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ActionExecutor")
def test_process_dialogue_turn_handles_greeting_intent(
    mock_action_executor_class: MagicMock,
    mock_short_term_memory_class: MagicMock,
):
    """Test that PFC correctly responds to a greeting intent."""
    mock_short_term_memory_instance = MagicMock(spec=ShortTermMemory)
    mock_short_term_memory_instance.get_conversation_context.return_value = {
        "dialogue_state": "IDLE",
        "interaction_count": 0,
        "user_id": str(uuid4()),
    }
    mock_short_term_memory_class.return_value = mock_short_term_memory_instance

    # MODIFIED: Instantiate PrefrontalCortex with the mocked dependencies
    pfc = PrefrontalCortex(
        short_term_memory=mock_short_term_memory_instance,
        action_executor=mock_action_executor_class.return_value,
    )

    nlu_results = {"intent": {"name": "greet", "confidence": 0.95}, "entities": {}}

    response = pfc.process_dialogue_turn(
        uuid4(), uuid4(), uuid4(), "hello", nlu_results
    )

    assert response["success"] is True
    assert response["va_response_text"] == "Hello! How can I help you today?"
    assert response["action_taken"] is None
    assert response["new_dialogue_state"] == "GREETING_INITIATED"

    # Verify context update
    args, kwargs = mock_short_term_memory_instance.update_conversation_context.call_args
    updated_context = args[1]
    assert updated_context["dialogue_state"] == "GREETING_INITIATED"
    assert updated_context["interaction_count"] == 1


@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ShortTermMemory")
@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ActionExecutor")
def test_process_dialogue_turn_handles_low_confidence_intent(
    mock_action_executor_class: MagicMock,
    mock_short_term_memory_class: MagicMock,
):
    """Test that PFC correctly responds to a low confidence intent."""
    mock_short_term_memory_instance = MagicMock(spec=ShortTermMemory)
    mock_short_term_memory_instance.get_conversation_context.return_value = {
        "dialogue_state": "IDLE",
        "interaction_count": 0,
        "user_id": str(uuid4()),
    }
    mock_short_term_memory_class.return_value = mock_short_term_memory_instance

    # MODIFIED: Instantiate PrefrontalCortex with the mocked dependencies
    pfc = PrefrontalCortex(
        short_term_memory=mock_short_term_memory_instance,
        action_executor=mock_action_executor_class.return_value,
    )

    # NLU results with low confidence
    nlu_results = {
        "intent": {"name": "unclear_intent", "confidence": 0.3},
        "entities": {},
    }

    response = pfc.process_dialogue_turn(
        uuid4(), uuid4(), uuid4(), "xyzzy", nlu_results
    )

    assert response["success"] is True
    assert response["va_response_text"] == (
        "I'm sorry, I didn't quite understand. Could you please rephrase that?"
    )
    assert response["action_taken"] is None
    assert response["new_dialogue_state"] == "ASKING_CLARIFICATION"

    # Verify context update
    args, kwargs = mock_short_term_memory_instance.update_conversation_context.call_args
    updated_context = args[1]
    assert updated_context["dialogue_state"] == "ASKING_CLARIFICATION"
    assert updated_context["interaction_count"] == 1


@patch("services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ShortTermMemory")
@patch(
    "services.brain.pre_forntal_cortex.src.pre_frontal_cortex.ActionExecutor"
)  # <-- NEW PATCH
def test_process_dialogue_turn_handles_default_unhandled_intent(
    mock_action_executor_class: MagicMock,  # <-- Order matters for patched arguments
    mock_short_term_memory_class: MagicMock,
):
    """Test that PFC handles an unhandled intent with a default response."""
    mock_short_term_memory_instance = MagicMock(spec=ShortTermMemory)
    mock_short_term_memory_instance.get_conversation_context.return_value = {
        "dialogue_state": "IDLE",
        "interaction_count": 0,
        "user_id": str(uuid4()),
    }
    mock_short_term_memory_class.return_value = mock_short_term_memory_instance

    # MODIFIED: Instantiate PrefrontalCortex with the mocked dependencies
    pfc = PrefrontalCortex(
        short_term_memory=mock_short_term_memory_instance,
        action_executor=mock_action_executor_class.return_value,
    )

    # NLU results with a confidence above low threshold but not matching 'greeting'
    nlu_results = {
        "intent": {"name": "unknown_topic", "confidence": 0.6},
        "entities": {},
    }

    response = pfc.process_dialogue_turn(
        uuid4(), uuid4(), uuid4(), "what is the meaning of life?", nlu_results
    )

    assert response["success"] is True
    assert response["va_response_text"] == (
        "I'm still learning, but I can help with a variety of tasks. "
        "What would you like to do?"
    )
    assert response["action_taken"] is None
    assert response["new_dialogue_state"] == "IDLE"

    # Verify context update
    args, kwargs = mock_short_term_memory_instance.update_conversation_context.call_args
    updated_context = args[1]
    assert updated_context["dialogue_state"] == "IDLE"
    assert updated_context["interaction_count"] == 1
