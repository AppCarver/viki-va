"""Test short term memory module."""

from uuid import uuid4

import pytest

from services.brain.short_term_mem.src.short_term_memory import ShortTermMemory


@pytest.fixture
def short_term_memory_instance() -> ShortTermMemory:
    """Provide a fresh ShortTermMemory instance for each test."""
    return ShortTermMemory()


def test_get_conversation_context_not_found(
    short_term_memory_instance: ShortTermMemory,
):
    """Test retrieving context for a non-existent conversation."""
    conversation_id = uuid4()
    context = short_term_memory_instance.get_conversation_context(conversation_id)
    assert context is None


def test_update_and_get_conversation_context(
    short_term_memory_instance: ShortTermMemory,
):
    """Test updating and then retrieving conversation context."""
    conversation_id = uuid4()
    initial_context = {
        "user_id": uuid4(),
        "active_goal": {"name": "book_flight"},
        "slots_filled": {"origin": "London"},
        "recent_turns": [{"speaker": "User", "text": "Hello!"}],
    }

    success = short_term_memory_instance.update_conversation_context(
        conversation_id, initial_context
    )
    assert success is True

    retrieved_context = short_term_memory_instance.get_conversation_context(
        conversation_id
    )
    assert retrieved_context is not None
    assert retrieved_context == initial_context


def test_update_conversation_context_overwrites_existing(
    short_term_memory_instance: ShortTermMemory,
):
    """Test that updating context for an existing ID overwrites the previous data."""
    conversation_id = uuid4()
    context_v1 = {"step": 1, "data": "initial"}
    context_v2 = {"step": 2, "data": "updated", "new_key": True}

    short_term_memory_instance.update_conversation_context(conversation_id, context_v1)
    success = short_term_memory_instance.update_conversation_context(
        conversation_id, context_v2
    )
    assert success is True

    retrieved_context = short_term_memory_instance.get_conversation_context(
        conversation_id
    )
    assert retrieved_context == context_v2
    assert retrieved_context != context_v1


def test_clear_conversation_context(
    short_term_memory_instance: ShortTermMemory,
):
    """Test clearing an existing conversation context."""
    conversation_id = uuid4()
    context_data = {"test_key": "test_value"}
    short_term_memory_instance.update_conversation_context(
        conversation_id, context_data
    )

    success = short_term_memory_instance.clear_conversation_context(conversation_id)
    assert success is True

    context_after_clear = short_term_memory_instance.get_conversation_context(
        conversation_id
    )
    assert context_after_clear is None


def test_clear_conversation_context_non_existent(
    short_term_memory_instance: ShortTermMemory,
):
    """Test clearing a non-existent conversation context."""
    conversation_id = uuid4()
    success = short_term_memory_instance.clear_conversation_context(conversation_id)
    assert success is False  # Should return False as nothing was cleared
