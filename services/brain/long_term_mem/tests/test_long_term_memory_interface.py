"""Tests for the LongTermMemoryInterface abstract base class.

These tests ensure that all abstract methods raise NotImplementedError
when called directly on the interface. This guarantees that subclasses
must implement these methods.
"""

from uuid import uuid4

import pytest

from services.brain.long_term_mem.src.long_term_memory_interface import (
    LongTermMemoryInterface,
)


def test_long_term_memory_interface_not_implemented():
    """Test that all abstract methods of.

    LongTermMemoryInterface raise NotImplementedError.

    This test calls each method directly on the interface and expects
    a NotImplementedError to be raised, confirming that the abstract
    interface cannot be used directly.
    """
    user_id = uuid4()
    with pytest.raises(NotImplementedError):
        LongTermMemoryInterface.store_fact(None, user_id, {})  # type: ignore
    with pytest.raises(NotImplementedError):
        LongTermMemoryInterface.retrieve_facts(None)  # type: ignore
    with pytest.raises(NotImplementedError):
        LongTermMemoryInterface.update_fact(None, user_id, {})  # type: ignore
    with pytest.raises(NotImplementedError):
        LongTermMemoryInterface.delete_fact(None, user_id)  # type: ignore
