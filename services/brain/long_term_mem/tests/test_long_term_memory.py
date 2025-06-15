"""Tests for the LongTermMemory component.

This module contains unit tests for the LongTermMemory class, ensuring correct
storage, retrieval, updating, and deletion of long-term memory facts, as well as
robust error handling and file persistence behaviors.
"""

import logging
import os
import shutil
import tempfile
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

# Corrected: Explicitly import LongTermMemory and LongTermMemoryError
from services.brain.long_term_mem.src.long_term_memory import LongTermMemory
from services.brain.long_term_mem.src.long_term_memory_interface import (
    LongTermMemoryInterface,
)
from shared_libs.errors.errors import LongTermMemoryError


@pytest.fixture
def temp_mem_file() -> Any:
    """Yield a temporary file path and clean up after test."""
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "test_mem.json")
    try:
        yield file_path
    finally:
        try:
            shutil.rmtree(temp_dir)
        except FileNotFoundError:
            pass


@pytest.fixture
def ltm_instance(temp_mem_file: str) -> Any:
    """Provide a fresh LongTermMemory instance for each test with a temp file."""
    return LongTermMemory(file_path=temp_mem_file)


def test_store_and_retrieve_fact(ltm_instance: Any) -> None:
    """Store a fact and retrieve it using user_id."""
    user_id = uuid4()
    fact_data = {"type": "preference", "key": "color", "value": "blue"}
    res = ltm_instance.store_fact(user_id, fact_data)
    assert res["success"] is True
    fact_id = res["fact_id"]
    # Retrieve by user_id
    res2 = ltm_instance.retrieve_facts(user_id)
    assert res2["success"] is True
    facts = res2["facts"]
    assert isinstance(facts, list)
    assert any(f["fact_id"] == str(fact_id) for f in facts)
    # Persistence
    ltm2 = LongTermMemory(ltm_instance.file_path)
    facts2 = ltm2.retrieve_facts(user_id)["facts"]
    assert any(f["fact_id"] == str(fact_id) for f in facts2)


def test_retrieve_with_query_criteria_and_limit(ltm_instance: Any) -> None:
    """Test retrieval with query criteria and result limiting."""
    user_id = uuid4()
    # Add two facts, different types
    fid1 = ltm_instance.store_fact(user_id, {"type": "a", "value": 1})["fact_id"]
    ltm_instance.store_fact(user_id, {"type": "b", "value": 2})
    # Query for type=a
    res = ltm_instance.retrieve_facts(user_id, query_criteria={"type": "a"})
    facts = res["facts"]
    assert len(facts) == 1 and facts[0]["fact_id"] == str(fid1)
    # Query for type not present
    facts_none = ltm_instance.retrieve_facts(user_id, query_criteria={"type": "c"})[
        "facts"
    ]
    assert facts_none == []
    # Query with limit
    facts_limit = ltm_instance.retrieve_facts(user_id, limit=1)["facts"]
    assert len(facts_limit) == 1


def test_retrieve_all_users(ltm_instance: Any) -> None:
    """Test retrieval of facts for all users."""
    u1, u2 = uuid4(), uuid4()
    f1 = ltm_instance.store_fact(u1, {"type": "foo"})["fact_id"]
    f2 = ltm_instance.store_fact(u2, {"type": "bar"})["fact_id"]
    all_facts = ltm_instance.retrieve_facts()["facts"]
    ids = {f["fact_id"] for f in all_facts}  # Use a set for robust comparison
    assert str(f1) in ids and str(f2) in ids


def test_retrieve_semantic_query_unimplemented(ltm_instance: Any, caplog: Any) -> None:
    """Test that semantic queries are unimplemented and return an empty result."""
    # Ensure memory is loaded for the instance
    ltm_instance.store_fact(uuid4(), {"content": "dummy"})
    with caplog.at_level(logging.WARNING):
        res = ltm_instance.retrieve_facts(semantic_query="meaning of life")
        assert res["success"] is True and res["facts"] == []
        assert "Semantic query feature is not yet implemented" in caplog.text


def test_retrieve_facts_handles_unexpected_error(
    monkeypatch: Any, ltm_instance: Any, caplog: Any
) -> None:
    """Test error handling when retrieve_facts encounters an unexpected error.

    Populate some dummy data so the iteration logic is attempted.
    """
    user_id = uuid4()
    ltm_instance.store_fact(user_id, {"key": "value"})

    # Simulate an unexpected error during fact retrieval (e.g., during
    # iteration over _memory). Replace the dictionary for this user_id with
    # a MagicMock that raises an error when its 'items' method is called.
    mock_user_memory = MagicMock()
    mock_user_memory.items.side_effect = Exception("simulated retrieval error")

    # Patch the specific user's entry in _memory
    monkeypatch.setitem(ltm_instance._memory, str(user_id), mock_user_memory)

    with caplog.at_level(logging.ERROR):
        result = ltm_instance.retrieve_facts(user_id=user_id)
        assert result["success"] is False
        assert result["facts"] == []
        assert result["error"]["code"] == "UNKNOWN_ERROR"
        assert "simulated retrieval error" in result["error"]["message"]
        assert "An unexpected error occurred while retrieving facts" in caplog.text


def test_update_fact_success_and_notfound(ltm_instance: Any) -> None:
    """Test successful update of a fact and handling of not found errors."""
    user_id = uuid4()
    fact = ltm_instance.store_fact(user_id, {"key": "k"})["fact_id"]
    # Update
    result = ltm_instance.update_fact(fact, {"value": "v"})
    assert result["success"] is True
    updated = ltm_instance.retrieve_facts(user_id)["facts"]
    assert any(f["fact_id"] == str(fact) and f["value"] == "v" for f in updated)
    # Not found
    result2 = ltm_instance.update_fact(uuid4(), {"foo": "bar"})
    assert result2["success"] is False
    assert result2["error"]["code"] == "NOT_FOUND"


def test_delete_fact_success_and_notfound(ltm_instance: Any) -> None:
    """Test successful deletion of a fact and handling of not found errors."""
    u = uuid4()
    fid = ltm_instance.store_fact(u, {"bar": "baz"})["fact_id"]
    result = ltm_instance.delete_fact(fid)
    assert result["success"] is True
    # Should be gone
    facts = ltm_instance.retrieve_facts(u)["facts"]
    assert not any(f["fact_id"] == str(fid) for f in facts)
    # Not found
    result2 = ltm_instance.delete_fact(uuid4())
    assert result2["success"] is False
    assert result2["error"]["code"] == "NOT_FOUND"


def test_store_fact_handles_errors(monkeypatch: Any, ltm_instance: Any) -> None:
    """Test error handling when storing a fact fails.

    Fails due to persistence or unknown errors.
    """
    user_id = uuid4()
    # Simulate persistence error
    monkeypatch.setattr(
        ltm_instance,
        "_save_memory",
        lambda: (_ for _ in ()).throw(LongTermMemoryError("fail")),
    )
    res = ltm_instance.store_fact(user_id, {"foo": "bar"})
    assert res["success"] is False and res["error"]["code"] == "PERSISTENCE_ERROR"
    # Simulate unknown error
    monkeypatch.setattr(
        ltm_instance, "_save_memory", lambda: (_ for _ in ()).throw(Exception("boom"))
    )
    res2 = ltm_instance.store_fact(user_id, {"foo": "bar"})
    assert res2["success"] is False and res2["error"]["code"] == "UNKNOWN_ERROR"


def test_update_fact_handles_errors(monkeypatch: Any, ltm_instance: Any) -> None:
    """Test error handling when updating a fact fails.

    Fails due to persistence or unknown errors.
    """
    user_id = uuid4()
    fact = ltm_instance.store_fact(user_id, {"a": 1})["fact_id"]
    # Simulate persistence error
    monkeypatch.setattr(
        ltm_instance,
        "_save_memory",
        lambda: (_ for _ in ()).throw(LongTermMemoryError("fail")),
    )
    res = ltm_instance.update_fact(fact, {"b": 2})
    assert res["success"] is False and res["error"]["code"] == "PERSISTENCE_ERROR"
    # Simulate unknown error
    monkeypatch.setattr(
        ltm_instance, "_save_memory", lambda: (_ for _ in ()).throw(Exception("fail"))
    )
    res2 = ltm_instance.update_fact(fact, {"c": 3})
    assert res2["success"] is False and res2["error"]["code"] == "UNKNOWN_ERROR"


def test_delete_fact_handles_errors(monkeypatch: Any, ltm_instance: Any) -> None:
    """Test error handling when deleting a fact fails.

    Fails due to persistence or unknown errors.
    """
    user_id = uuid4()
    fid = ltm_instance.store_fact(user_id, {"foo": "bar"})["fact_id"]

    # Store the original _save_memory method before patching
    original_save_memory_method = ltm_instance._save_memory

    # Simulate persistence error
    monkeypatch.setattr(
        ltm_instance,
        "_save_memory",
        lambda: (_ for _ in ()).throw(LongTermMemoryError("fail")),
    )
    res = ltm_instance.delete_fact(fid)
    assert res["success"] is False and res["error"]["code"] == "PERSISTENCE_ERROR"

    # Restore original _save_memory so we can add a new fact and simulate the next error
    monkeypatch.setattr(ltm_instance, "_save_memory", original_save_memory_method)

    fid2 = ltm_instance.store_fact(user_id, {"foo": "baz"})["fact_id"]
    # Now simulate unknown error
    monkeypatch.setattr(
        ltm_instance, "_save_memory", lambda: (_ for _ in ()).throw(Exception("fail"))
    )
    res2 = ltm_instance.delete_fact(fid2)
    assert res2["success"] is False and res2["error"]["code"] == "UNKNOWN_ERROR"


def test_load_memory_handles_errors(
    tmp_path: Any, monkeypatch: Any, caplog: Any
) -> None:
    """Test error handling during memory loading.

    Handles bad JSON, OSError, or unknown exceptions.
    """
    # Test 1: Bad JSON
    file_path_bad_json = tmp_path / "bad.json"
    file_path_bad_json.write_text("not a json")
    with caplog.at_level(logging.ERROR):
        ltm = LongTermMemory(str(file_path_bad_json))
        assert ltm._memory == {}
        assert "Error decoding JSON" in caplog.text

    # Test 2: Simulate OSError on file open
    file_path_os_error = tmp_path / "os_error.json"
    # Ensure the file exists so open is actually called
    file_path_os_error.write_text('{"dummy":"data"}')

    with monkeypatch.context() as m:
        m.setattr("builtins.open", MagicMock(side_effect=OSError("mock os error")))
        with caplog.at_level(logging.ERROR):
            ltm2 = LongTermMemory(str(file_path_os_error))
            assert ltm2._memory == {}
            assert "I/O error loading memory" in caplog.text

    # Test 3: Simulate unknown error on json.load
    file_path_unknown_error = tmp_path / "unknown_error.json"
    file_path_unknown_error.write_text('{"dummy":"data"}')
    with monkeypatch.context() as m:
        m.setattr(
            "json.load", MagicMock(side_effect=Exception("mock unexpected error"))
        )
        with caplog.at_level(logging.ERROR):
            ltm3 = LongTermMemory(str(file_path_unknown_error))
            assert ltm3._memory == {}
            assert "An unexpected error occurred while loading memory" in caplog.text


def test_save_memory_handles_errors(
    monkeypatch: Any, temp_mem_file: str, caplog: Any
) -> None:
    """Test error handling during saving memory.

    Handles OSError or unknown exceptions.
    """
    ltm = LongTermMemory(temp_mem_file)
    ltm._memory = {"user": {"fact": {"content": "test"}}}  # Populate memory to be saved

    # Test 1: Simulate OSError on os.makedirs
    with monkeypatch.context() as m:
        m.setattr(
            "os.makedirs", MagicMock(side_effect=OSError("mock os error makedirs"))
        )
        with caplog.at_level(logging.ERROR):
            with pytest.raises(
                LongTermMemoryError, match="Failed to save memory due to I/O error"
            ):
                ltm._save_memory()
            assert "I/O error saving memory" in caplog.text
        caplog.clear()  # Clear logs for next test

    # Test 2: Simulate unknown error on json.dump
    with monkeypatch.context() as m:
        m.setattr(
            "json.dump", MagicMock(side_effect=Exception("mock unknown dump error"))
        )
        with caplog.at_level(logging.ERROR):
            with pytest.raises(
                LongTermMemoryError,
                match="Failed to save memory due to unexpected error",
            ):
                ltm._save_memory()
            assert "An unexpected error occurred while saving memory" in caplog.text


# --- Tests for LongTermMemoryInterface (moved here for consolidation) ---


class TestLongTermMemoryInterface:
    """Tests for the LongTermMemoryInterface abstract class."""

    def test_interface_instantiation(self) -> None:
        """Test that subclassing LongTermMemoryInterface.

        Enforces method implementation.
        """

        class DummyLTM(LongTermMemoryInterface):
            def store_fact(
                self,
                user_id: UUID,
                fact_data: dict[str, Any],
                retention_policy: str | None = None,
            ) -> dict[str, Any]:
                return {"success": True}

            def retrieve_facts(
                self,
                user_id: UUID | None = None,
                query_criteria: dict[str, Any] | None = None,
                limit: int | None = None,
                semantic_query: str | None = None,
            ) -> dict[str, Any]:
                return {"success": True, "facts": []}

            def update_fact(
                self, fact_id: UUID, updated_data: dict[str, Any]
            ) -> dict[str, Any]:
                return {"success": True}

            def delete_fact(self, fact_id: UUID) -> dict[str, Any]:
                return {"success": True}

        dummy = DummyLTM()
        assert hasattr(dummy, "store_fact")
        assert hasattr(dummy, "retrieve_facts")
        assert hasattr(dummy, "update_fact")
        assert hasattr(dummy, "delete_fact")

    def test_interface_methods_raise_not_implemented(self) -> None:
        """Test interface abstract methods raise NotImplementedError."""
        with pytest.raises(TypeError):
            # This is how ABCs prevent direct instantiation
            LongTermMemoryInterface()  # type: ignore

        user_id = uuid4()
        with pytest.raises(NotImplementedError):
            LongTermMemoryInterface.store_fact(None, user_id, {})  # type: ignore
        with pytest.raises(NotImplementedError):
            LongTermMemoryInterface.retrieve_facts(None)  # type: ignore
        with pytest.raises(NotImplementedError):
            LongTermMemoryInterface.update_fact(None, user_id, {})  # type: ignore
        with pytest.raises(NotImplementedError):
            LongTermMemoryInterface.delete_fact(None, user_id)  # type: ignore
