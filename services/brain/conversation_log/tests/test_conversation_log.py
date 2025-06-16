"""Test Viki's Conversation Log component using a MongoDB backend.

This module contains unit tests for the ConversationLog class,
covering its core functionalities including logging turns, and
retrieving turns by conversation, user, and time range.
It mocks MongoDB interactions using mongomock for isolated testing.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock  # Added MagicMock import
from uuid import uuid4

import pytest

# Using mongomock for in-memory MongoDB simulation in tests
from mongomock import MongoClient as MockMongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from pytest import MonkeyPatch

# Import the ConversationLog and ConversationTurn from the source module
from services.brain.conversation_log.src.conversation_log import ConversationLog
from services.brain.conversation_log.src.conversation_log_interface import (
    ConversationTurn,
)


# Fixture to mock MongoClient for all tests in this module
# This ensures tests run quickly without needing a real MongoDB instance
@pytest.fixture(autouse=True)
def mock_mongo_client(monkeypatch: MonkeyPatch) -> None:
    """Mock pymongo.MongoClient to use mongomock's in-memory client.

    Also mocks the admin.command('ismaster') call which is not implemented
    in mongomock by default, preventing NotImplementedError during connection
    checks.
    """
    # Create a mock client instance
    mock_client_instance: MockMongoClient = MockMongoClient()

    # Mock the admin.command method to return a success for 'ismaster'
    mock_admin_db = mock_client_instance.admin
    # Ensure a proper return value that satisfies pymongo's connection check
    monkeypatch.setattr(
        mock_admin_db,
        "command",
        lambda cmd, **kwargs: {"ok": 1.0} if cmd == "ismaster" else {},
    )

    # Set up the mock client to point to the mongomock's MongoClient
    # This ensures that when ConversationLog tries to instantiate MongoClient,
    # it gets our mock instead.
    monkeypatch.setattr(
        "services.brain.conversation_log.src.conversation_log.MongoClient",
        lambda *args, **kwargs: mock_client_instance,
    )


@pytest.fixture
def conversation_log_instance() -> ConversationLog:
    """Provide a fresh ConversationLog instance for each test.

    Uses the mocked MongoClient, so it's in-memory and isolated.
    """
    return ConversationLog(mongo_host="mock_host", mongo_port=12345)


@pytest.fixture
def example_conversation_turns() -> list[ConversationTurn]:
    """Provide a list of example ConversationTurn objects for testing."""
    user_id_1 = uuid4()
    user_id_2 = uuid4()
    conv_id_1 = uuid4()
    conv_id_2 = uuid4()

    # Create turns with distinct timestamps for ordering tests
    base_time = datetime(2025, 1, 1, 10, 0, 0, tzinfo=UTC)

    turns: list[ConversationTurn] = [
        ConversationTurn(
            turn_id=uuid4(),
            conversation_id=conv_id_1,
            user_id=user_id_1,
            timestamp=base_time + timedelta(seconds=1),
            speaker="user",
            text="Hello Viki!",
        ),
        ConversationTurn(
            turn_id=uuid4(),
            conversation_id=conv_id_1,
            user_id=user_id_1,
            timestamp=base_time + timedelta(seconds=2),
            speaker="viki",
            text="Hi there! How can I help you today?",
        ),
        ConversationTurn(
            turn_id=uuid4(),
            conversation_id=conv_id_1,
            user_id=user_id_1,
            timestamp=base_time + timedelta(seconds=3),
            speaker="user",
            text="What's the weather like?",
        ),
        ConversationTurn(
            turn_id=uuid4(),
            conversation_id=conv_id_2,
            user_id=user_id_1,
            timestamp=base_time + timedelta(seconds=4),
            speaker="user",
            text="Start a new conversation, same user.",
        ),
        ConversationTurn(
            turn_id=uuid4(),
            conversation_id=conv_id_2,
            user_id=user_id_1,
            timestamp=base_time + timedelta(seconds=5),
            speaker="viki",
            text="Sure, new topic for you!",
        ),
        ConversationTurn(
            turn_id=uuid4(),
            conversation_id=uuid4(),  # Different conversation for user 2
            user_id=user_id_2,
            timestamp=base_time + timedelta(seconds=6),
            speaker="user",
            text="Hello from another user!",
        ),
        ConversationTurn(
            turn_id=uuid4(),
            conversation_id=uuid4(),  # Another different conversation for user 2
            user_id=user_id_2,
            timestamp=base_time + timedelta(seconds=7),
            speaker="viki",
            text="Welcome, new user!",
        ),
    ]
    return turns


class TestConversationLog:
    """Unit tests for the ConversationLog component."""

    def test_init_success(self, conversation_log_instance: ConversationLog) -> None:
        """Test successful initialization and MongoDB connection."""
        assert conversation_log_instance._client is not None
        assert conversation_log_instance._db is not None
        assert conversation_log_instance._collection is not None
        assert isinstance(conversation_log_instance._client, MockMongoClient)

    def test_init_connection_failure(
        self, monkeypatch: MonkeyPatch, caplog: Any
    ) -> None:
        """Test initialization failure when MongoDB connection fails."""

        # Mock MongoClient to return a client that will cause ConnectionFailure
        # when _connect_to_mongodb calls admin.command('ismaster')
        class MockClientFailure:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            @property
            def admin(self) -> Any:
                mock_admin = MagicMock()
                mock_admin.command.side_effect = ConnectionFailure(
                    "Simulated connection error"
                )
                return mock_admin

        monkeypatch.setattr(
            "services.brain.conversation_log.src.conversation_log.MongoClient",
            MockClientFailure,
        )

        with caplog.at_level(logging.ERROR):
            # We now expect init to not raise, but _collection to be None
            log_service = ConversationLog()
            assert log_service._collection is None
            assert "Failed to connect to MongoDB" in caplog.text

    def test_init_unexpected_error(self, monkeypatch: MonkeyPatch, caplog: Any) -> None:
        """Test initialization failure for unexpected errors during connection."""

        # Mock MongoClient to raise a generic Exception during its instantiation
        def mock_mongo_client_unexpected_fail(*args: Any, **kwargs: Any) -> None:
            raise ValueError("Unexpected error during client creation")

        monkeypatch.setattr(
            "services.brain.conversation_log.src.conversation_log.MongoClient",
            mock_mongo_client_unexpected_fail,
        )

        with caplog.at_level(logging.ERROR):
            # We now expect init to not raise, but _collection to be None
            log_service = ConversationLog()
            assert log_service._collection is None
            assert (
                "An unexpected error occurred during MongoDB connection" in caplog.text
            )

    def test_log_turn_success(
        self, conversation_log_instance: ConversationLog, caplog: Any
    ) -> None:
        """Test successful logging of a conversation turn."""
        turn = ConversationTurn(
            turn_id=uuid4(),
            conversation_id=uuid4(),
            user_id=uuid4(),
            timestamp=datetime.now(UTC),
            speaker="user",
            text="Test message",
        )

        with caplog.at_level(logging.INFO):
            result = conversation_log_instance.log_turn(turn)

            assert result["success"] is True
            assert result["turn_id"] == turn.turn_id
            assert result["error"] is None

            # Verify the turn is in the mock collection
            assert (
                conversation_log_instance._collection is not None
            )  # Narrow type for mypy
            doc = conversation_log_instance._collection.find_one(
                {"turn_id": str(turn.turn_id)}
            )
            assert doc is not None
            assert doc["text"] == "Test message"
            # Reconstruct ConversationTurn from the doc to verify timestamp type
            retrieved_turn_obj = ConversationTurn.from_dict(doc)
            assert isinstance(retrieved_turn_obj.timestamp, datetime)
            assert "logged for user" in caplog.text

    def test_log_turn_persistence_error(
        self,
        conversation_log_instance: ConversationLog,
        monkeypatch: MonkeyPatch,
        caplog: Any,
    ) -> None:
        """Test logging failure due to PyMongoError during insert."""
        turn = ConversationTurn(
            turn_id=uuid4(),
            conversation_id=uuid4(),
            user_id=uuid4(),
            timestamp=datetime.now(UTC),
            speaker="user",
            text="Failing message",
        )

        # Mock insert_one to raise a PyMongoError
        def mock_insert_one_fail(*args: Any, **kwargs: Any) -> None:
            raise PyMongoError("Simulated write error")

        monkeypatch.setattr(
            conversation_log_instance._collection, "insert_one", mock_insert_one_fail
        )

        with caplog.at_level(logging.ERROR):
            result = conversation_log_instance.log_turn(turn)

            assert result["success"] is False
            assert result["error"]["code"] == "PERSISTENCE_ERROR"
            assert "Simulated write error" in result["error"]["message"]
            assert "PyMongo error logging conversation turn" in caplog.text

    def test_log_turn_unexpected_error(
        self,
        conversation_log_instance: ConversationLog,
        monkeypatch: MonkeyPatch,
        caplog: Any,
    ) -> None:
        """Test logging failure due to unexpected generic error."""
        turn = ConversationTurn(
            turn_id=uuid4(),
            conversation_id=uuid4(),
            user_id=uuid4(),
            timestamp=datetime.now(UTC),
            speaker="user",
            text="Unexpected error message",
        )

        # Mock the `to_dict` method of the turn object to raise an unexpected error.
        # This simulates an error occurring within the try block of log_turn,
        # but not a PyMongoError.
        def mock_to_dict_fail() -> None:
            raise ValueError("Simulated unexpected to_dict error")

        monkeypatch.setattr(turn, "to_dict", mock_to_dict_fail)

        with caplog.at_level(logging.ERROR):
            result = conversation_log_instance.log_turn(turn)

            assert result["success"] is False
            assert result["error"]["code"] == "UNKNOWN_ERROR"
            assert "Simulated unexpected to_dict error" in result["error"]["message"]
            assert "An unexpected error occurred while logging turn" in caplog.text

    def test_log_turn_not_initialized(
        self, conversation_log_instance: ConversationLog, caplog: Any
    ) -> None:
        """Test logging when the MongoDB collection is not initialized."""
        conversation_log_instance._collection = None  # Manually un-initialize
        turn = ConversationTurn(
            turn_id=uuid4(),
            conversation_id=uuid4(),
            user_id=uuid4(),
            timestamp=datetime.now(UTC),
            speaker="user",
            text="Should fail",
        )

        with caplog.at_level(logging.ERROR):
            result = conversation_log_instance.log_turn(turn)
            assert result["success"] is False
            assert result["error"]["code"] == "SERVICE_UNAVAILABLE"
            assert "MongoDB not connected." in result["error"]["message"]
            assert "MongoDB collection not initialized." in caplog.text

    @pytest.mark.parametrize(
        "limit, offset, expected_count, expected_first_text",
        [
            (None, None, 3, "Hello Viki!"),  # All turns
            (2, None, 2, "Hello Viki!"),  # Limit only
            (None, 1, 2, "Hi there! How can I help you today?"),  # Offset only
            (1, 1, 1, "Hi there! How can I help you today?"),  # Limit and offset
            (1, 0, 1, "Hello Viki!"),  # Limit 1, offset 0
            (10, 0, 3, "Hello Viki!"),  # Limit > actual, offset 0
            (1, 2, 1, "What's the weather like?"),  # Limit 1, offset 2
            (1, 3, 0, None),  # Offset beyond count
        ],
    )
    def test_get_conversation_turns_filters(
        self,
        conversation_log_instance: ConversationLog,
        example_conversation_turns: list[ConversationTurn],
        limit: int | None,
        offset: int | None,
        expected_count: int,
        expected_first_text: str | None,
    ) -> None:
        """Test retrieving conversation turns with limit and offset."""
        # Log all example turns
        for turn in example_conversation_turns:
            conversation_log_instance.log_turn(turn)

        # Assuming conv_id_1 from example_conversation_turns (first 3 turns)
        conv_id_1 = example_conversation_turns[0].conversation_id

        result = conversation_log_instance.get_conversation_turns(
            conv_id_1, limit=limit, offset=offset
        )

        assert result["success"] is True
        assert result["error"] is None
        assert len(result["history"]) == expected_count

        if expected_count > 0:
            assert result["history"][0].text == expected_first_text
            # Verify turns are sorted by timestamp
            for i in range(len(result["history"]) - 1):
                assert (
                    result["history"][i].timestamp <= result["history"][i + 1].timestamp
                )

    def test_get_conversation_turns_timestamp_filter(
        self,
        conversation_log_instance: ConversationLog,
        example_conversation_turns: list[ConversationTurn],
    ) -> None:
        """Test retrieving conversation turns with timestamp filters."""
        for turn in example_conversation_turns:
            conversation_log_instance.log_turn(turn)

        conv_id_1 = example_conversation_turns[0].conversation_id

        # Get turns between first and third turn (exclusive on start, inclusive on end)
        from_ts = example_conversation_turns[0].timestamp + timedelta(microseconds=1)
        to_ts = example_conversation_turns[2].timestamp

        result = conversation_log_instance.get_conversation_turns(
            conv_id_1, from_timestamp=from_ts, to_timestamp=to_ts
        )

        assert result["success"] is True
        assert result["error"] is None
        assert len(result["history"]) == 2  # Should get turn2 and turn3
        assert result["history"][0].text == ("Hi there! How can I help you today?")
        assert result["history"][1].text == "What's the weather like?"

        # Test only from_timestamp
        result_from = conversation_log_instance.get_conversation_turns(
            conv_id_1, from_timestamp=example_conversation_turns[1].timestamp
        )
        assert len(result_from["history"]) == 2
        assert result_from["history"][0].text == ("Hi there! How can I help you today?")

        # Test only to_timestamp
        result_to = conversation_log_instance.get_conversation_turns(
            conv_id_1, to_timestamp=example_conversation_turns[1].timestamp
        )
        assert len(result_to["history"]) == 2
        assert result_to["history"][0].text == "Hello Viki!"
        assert result_to["history"][1].text == ("Hi there! How can I help you today?")

    def test_get_conversation_turns_non_existent_conversation(
        self,
        conversation_log_instance: ConversationLog,
        example_conversation_turns: list[ConversationTurn],
    ) -> None:
        """Test retrieving turns for a conversation that does not exist."""
        for turn in example_conversation_turns:
            conversation_log_instance.log_turn(turn)

        non_existent_conv_id = uuid4()
        result = conversation_log_instance.get_conversation_turns(non_existent_conv_id)

        assert result["success"] is True
        assert result["error"] is None
        assert len(result["history"]) == 0

    def test_get_conversation_turns_persistence_error(
        self,
        conversation_log_instance: ConversationLog,
        monkeypatch: MonkeyPatch,
        caplog: Any,
    ) -> None:
        """Test retrieval failure due to PyMongoError."""

        # Mock find to raise a PyMongoError
        def mock_find_fail(*args: Any, **kwargs: Any) -> Any:
            raise PyMongoError("Simulated read error")

        monkeypatch.setattr(
            conversation_log_instance._collection, "find", mock_find_fail
        )

        with caplog.at_level(logging.ERROR):
            result = conversation_log_instance.get_conversation_turns(uuid4())

            assert result["success"] is False
            assert result["history"] == []
            assert result["error"]["code"] == "RETRIEVAL_ERROR"
            assert "Simulated read error" in result["error"]["message"]
            assert "PyMongo error retrieving turns" in caplog.text

    def test_get_conversation_turns_unexpected_error(
        self,
        conversation_log_instance: ConversationLog,
        monkeypatch: MonkeyPatch,
        caplog: Any,
    ) -> None:
        """Test retrieval failure due to unexpected generic error."""

        # Mock find to raise a generic Exception
        def mock_find_unexpected_fail(*args: Any, **kwargs: Any) -> Any:
            raise ValueError("Unexpected error during find operation")

        monkeypatch.setattr(
            conversation_log_instance._collection, "find", mock_find_unexpected_fail
        )

        with caplog.at_level(logging.ERROR):
            result = conversation_log_instance.get_conversation_turns(uuid4())

            assert result["success"] is False
            assert result["history"] == []
            assert result["error"]["code"] == "UNKNOWN_ERROR"
            assert (
                "Unexpected error during find operation" in result["error"]["message"]
            )
            assert "An unexpected error occurred while retrieving turns" in caplog.text

    def test_get_conversation_turns_not_initialized(
        self, conversation_log_instance: ConversationLog, caplog: Any
    ) -> None:
        """Test retrieval when MongoDB collection is not initialized."""
        conversation_log_instance._collection = None  # Manually un-initialize

        with caplog.at_level(logging.ERROR):
            result = conversation_log_instance.get_conversation_turns(uuid4())
            assert result["success"] is False
            assert result["error"]["code"] == "SERVICE_UNAVAILABLE"
            assert "MongoDB not connected." in result["error"]["message"]
            assert "MongoDB collection not initialized." in caplog.text

    @pytest.mark.parametrize(
        "limit, expected_count, expected_first_text",
        [
            (None, 5, "Sure, new topic for you!"),  # All turns for user 1
            (2, 2, "Sure, new topic for you!"),  # Limit 2 for user 1
            (1, 1, "Sure, new topic for you!"),  # Limit 1 for user 1
            (10, 5, "Sure, new topic for you!"),  # Limit > actual for user 1
        ],
    )
    def test_get_recent_user_turns_filters(
        self,
        conversation_log_instance: ConversationLog,
        example_conversation_turns: list[ConversationTurn],
        limit: int | None,
        expected_count: int,
        expected_first_text: str,
    ) -> None:
        """Test retrieving recent user turns with limit."""
        for turn in example_conversation_turns:
            conversation_log_instance.log_turn(turn)

        user_id_1 = example_conversation_turns[0].user_id

        result = conversation_log_instance.get_recent_user_turns(user_id_1, limit=limit)

        assert result["success"] is True
        assert result["error"] is None
        assert len(result["history"]) == expected_count

        if expected_count > 0:
            assert result["history"][0].text == expected_first_text
            # Verify turns are sorted by timestamp in descending order (newest first)
            for i in range(len(result["history"]) - 1):
                assert (
                    result["history"][i].timestamp >= result["history"][i + 1].timestamp
                )

    def test_get_recent_user_turns_non_existent_user(
        self,
        conversation_log_instance: ConversationLog,
        example_conversation_turns: list[ConversationTurn],
    ) -> None:
        """Test retrieving recent turns for a user that does not exist."""
        for turn in example_conversation_turns:
            conversation_log_instance.log_turn(turn)

        non_existent_user_id = uuid4()
        result = conversation_log_instance.get_recent_user_turns(non_existent_user_id)

        assert result["success"] is True
        assert result["error"] is None
        assert len(result["history"]) == 0

    def test_get_recent_user_turns_persistence_error(
        self,
        conversation_log_instance: ConversationLog,
        monkeypatch: MonkeyPatch,
        caplog: Any,
    ) -> None:
        """Test recent user turns retrieval failure due to PyMongoError."""

        # Mock find to raise a PyMongoError
        def mock_find_fail(*args: Any, **kwargs: Any) -> Any:
            raise PyMongoError("Simulated read error")

        monkeypatch.setattr(
            conversation_log_instance._collection, "find", mock_find_fail
        )

        with caplog.at_level(logging.ERROR):
            result = conversation_log_instance.get_recent_user_turns(uuid4())

            assert result["success"] is False
            assert result["history"] == []
            assert result["error"]["code"] == "RETRIEVAL_ERROR"
            assert "Simulated read error" in result["error"]["message"]
            assert "PyMongo error retrieving recent turns" in caplog.text

    def test_get_recent_user_turns_unexpected_error(
        self,
        conversation_log_instance: ConversationLog,
        monkeypatch: MonkeyPatch,
        caplog: Any,
    ) -> None:
        """Test recent user turns retrieval failure due to unexpected generic error."""

        # Mock find to raise a generic Exception
        def mock_find_unexpected_fail(*args: Any, **kwargs: Any) -> Any:
            raise ValueError("Unexpected error during find operation")

        monkeypatch.setattr(
            conversation_log_instance._collection, "find", mock_find_unexpected_fail
        )

        with caplog.at_level(logging.ERROR):
            result = conversation_log_instance.get_recent_user_turns(uuid4())

            assert result["success"] is False
            assert result["history"] == []
            assert result["error"]["code"] == "UNKNOWN_ERROR"
            assert (
                "Unexpected error during find operation" in result["error"]["message"]
            )
            assert (
                "An unexpected error occurred while retrieving recent turns"
                in caplog.text
            )

    def test_get_recent_user_turns_not_initialized(
        self, conversation_log_instance: ConversationLog, caplog: Any
    ) -> None:
        """Test retrieval when MongoDB collection is not initialized."""
        conversation_log_instance._collection = None  # Manually un-initialize

        with caplog.at_level(logging.ERROR):
            result = conversation_log_instance.get_recent_user_turns(uuid4())
            assert result["success"] is False
            assert result["error"]["code"] == "SERVICE_UNAVAILABLE"
            assert "MongoDB not connected." in result["error"]["message"]
            assert "MongoDB collection not initialized." in caplog.text
