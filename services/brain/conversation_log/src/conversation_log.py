"""Manage Viki's conversation log using MongoDB.

This component stores, retrieves, and provides access to immutable conversation
turn records, acting as the single source of truth for conversational history.
It adheres to the ConversationLogInterface and is designed for local or
centralized deployment.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

# Import the ConversationLogInterface and ConversationTurn from the interface file
# Assuming conversation_log_interface.py is in the same directory or accessible
from services.brain.conversation_log.src.conversation_log_interface import (
    ConversationLogInterface,
    ConversationTurn,
)


class ConversationLog(ConversationLogInterface):
    """Manage Viki's conversation log using MongoDB.

    This component stores, retrieves, and provides access to immutable
    conversation turn records, acting as the single source of truth for
    conversational history. It adheres to the ConversationLogInterface.
    """

    # Default MongoDB connection parameters
    DEFAULT_MONGO_HOST: str = "localhost"
    DEFAULT_MONGO_PORT: int = 27017
    DB_NAME: str = "viki_conversation_log"
    COLLECTION_NAME: str = "conversation_turns"

    def __init__(
        self,
        mongo_host: str = DEFAULT_MONGO_HOST,
        mongo_port: int = DEFAULT_MONGO_PORT,
        db_name: str = DB_NAME,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        """Initialize the ConversationLog component.

        Connects to MongoDB and sets up the logger.

        Args:
        ----
            mongo_host (str): The hostname or IP address of the MongoDB server.
            mongo_port (int): The port number of the MongoDB server.
            db_name (str): The name of the MongoDB database to use.
            collection_name (str): The name of the collection to store turns in.

        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client: MongoClient | None = None
        self._db = None
        self._collection = None
        self._mongo_host = mongo_host
        self._mongo_port = mongo_port
        self._db_name = db_name
        self._collection_name = collection_name

        # Attempt to connect; __init__ will not raise on connection failure
        # Removed inline tuple type annotation as mypy can infer it from the
        # function's return.
        connected, client, db, collection = self._connect_to_mongodb()
        if connected:
            self._client = client
            self._db = db
            self._collection = collection
            self.logger.info("ConversationLog initialized and connected to MongoDB.")
        else:
            self._client = None
            self._db = None
            self._collection = None
            self.logger.error(
                "ConversationLog initialized but failed to connect to MongoDB."
            )

    def _connect_to_mongodb(
        self,
    ) -> tuple[bool, MongoClient | None, Any | None, Any | None]:
        """Attempt to establish a connection to the MongoDB server.

        Returns a tuple (success: bool, client, db, collection).
        """
        try:
            client: MongoClient = MongoClient(
                self._mongo_host, self._mongo_port, serverSelectionTimeoutMS=5000
            )
            # The ismaster command is cheap and does not require auth.
            client.admin.command("ismaster")
            db = client[self._db_name]
            collection = db[self._collection_name]
            self.logger.info(
                f"Successfully connected to MongoDB at "
                f"{self._mongo_host}:{self._mongo_port}/"
                f"{self._db_name}/{self._collection_name}"
            )
            return True, client, db, collection
        except ConnectionFailure as e:
            self.logger.error(
                f"Failed to connect to MongoDB at "
                f"{self._mongo_host}:{self._mongo_port}: {e}"
            )
            return False, None, None, None
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred during MongoDB connection: {e}"
            )
            return False, None, None, None

    def log_turn(self, turn: ConversationTurn) -> dict[str, Any]:
        """Store a new conversation turn record in MongoDB.

        This operation is designed to be immutable; we only insert.
        """
        if not self._collection:
            self.logger.error("MongoDB collection not initialized.")
            return {
                "success": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "MongoDB not connected.",
                },
            }
        else:  # Explicit else block added
            try:
                assert self._collection is not None
                # Prepare data for MongoDB insertion.
                # ConversationTurn.to_dict() now handles ISO string conversion.
                turn_data = turn.to_dict()

                insert_result = self._collection.insert_one(turn_data)

                # The _id of the inserted document is typically used as the primary
                # identifier in MongoDB. We return the UUID from the turn object
                # as per interface.
                self.logger.info(
                    f"Turn '{turn.turn_id}' logged for user '{turn.user_id}' "
                    f"in conversation '{turn.conversation_id}' "
                    f"with MongoDB _id: {insert_result.inserted_id}."
                )
                return {"success": True, "turn_id": turn.turn_id, "error": None}
            except PyMongoError as e:
                self.logger.exception(
                    f"PyMongo error logging conversation turn '{turn.turn_id}'."
                )
                return {
                    "success": False,
                    "error": {
                        "code": "PERSISTENCE_ERROR",
                        "message": f"MongoDB write failed: {e}",
                    },
                }
            except Exception as e:
                self.logger.exception(
                    f"An unexpected error occurred while logging turn '{turn.turn_id}'."
                )
                return {
                    "success": False,
                    "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
                }

    def get_conversation_turns(
        self,
        conversation_id: UUID,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Retrieve a sequence of ConversationTurn records.

        For a specific conversation.
        """
        if not self._collection:
            self.logger.error("MongoDB collection not initialized.")
            return {
                "success": False,
                "history": [],
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "MongoDB not connected.",
                },
            }
        else:  # Explicit else block added
            try:
                assert self._collection is not None

                query_filter: dict[str, Any] = {"conversation_id": str(conversation_id)}

                timestamp_filter: dict[str, Any] = {}
                if from_timestamp:
                    # When querying, MongoDB expects datetime objects for datetime
                    # fields. Ensure the stored timestamp (ISO string) is compared
                    # correctly.PyMongo will handle the comparison correctly if
                    # the field in DB is also ISO string.
                    timestamp_filter["$gte"] = from_timestamp.isoformat()
                if to_timestamp:
                    timestamp_filter["$lte"] = to_timestamp.isoformat()

                if timestamp_filter:
                    query_filter["timestamp"] = timestamp_filter

                # Build the cursor with sort, skip, and limit
                cursor = self._collection.find(query_filter).sort("timestamp", 1)
                # Ascending by timestamp (ISO string sorting works lexicographically)

                if offset is not None:
                    cursor = cursor.skip(offset)
                if limit is not None:
                    cursor = cursor.limit(limit)

                # Retrieve documents and convert them to ConversationTurn objects.
                # from_dict expects ISO string, which is how we now store it.
                retrieved_turns = [ConversationTurn.from_dict(doc) for doc in cursor]

                self.logger.info(
                    f"Retrieved {len(retrieved_turns)} turns for conversation "
                    f"'{conversation_id}' with filters."
                )
                return {"success": True, "history": retrieved_turns, "error": None}
            except PyMongoError as e:
                self.logger.exception(
                    f"PyMongo error retrieving turns for conversation "
                    f"'{conversation_id}'."
                )
                return {
                    "success": False,
                    "history": [],
                    "error": {
                        "code": "RETRIEVAL_ERROR",
                        "message": f"MongoDB read failed: {e}",
                    },
                }
            except Exception as e:
                self.logger.exception(
                    f"An unexpected error occurred while retrieving turns for "
                    f"conversation '{conversation_id}'."
                )
                return {
                    "success": False,
                    "history": [],
                    "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
                }

    def get_recent_user_turns(
        self, user_id: UUID, limit: int | None = None
    ) -> dict[str, Any]:
        """Retrieve the most recent ConversationTurns.

        Across all conversations for a given user.
        """
        if not self._collection:
            self.logger.error("MongoDB collection not initialized.")
            return {
                "success": False,
                "history": [],
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "MongoDB not connected.",
                },
            }
        else:  # Explicit else block added
            try:
                assert self._collection is not None

                query_filter: dict[str, Any] = {"user_id": str(user_id)}

                # Sort by timestamp in descending order (newest first)
                cursor = self._collection.find(query_filter).sort("timestamp", -1)

                if limit is not None:
                    cursor = cursor.limit(limit)

                recent_turns = [ConversationTurn.from_dict(doc) for doc in cursor]

                self.logger.info(
                    f"Retrieved {len(recent_turns)} recent turns for user '{user_id}'."
                )
                return {"success": True, "history": recent_turns, "error": None}
            except PyMongoError as e:
                self.logger.exception(
                    f"PyMongo error retrieving recent turns for user '{user_id}'."
                )
                return {
                    "success": False,
                    "history": [],
                    "error": {
                        "code": "RETRIEVAL_ERROR",
                        "message": f"MongoDB read failed: {e}",
                    },
                }
            except Exception as e:
                self.logger.exception(
                    f"An unexpected error occurred while retrieving recent turns "
                    f"for user '{user_id}'."
                )
                return {
                    "success": False,
                    "history": [],
                    "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
                }


# Example usage (for local testing, will be removed for actual tests)
if __name__ == "__main__":  # pragma: no cover
    import time
    from datetime import timedelta

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Instantiate ConversationLog (connects to local MongoDB)
    log_service = ConversationLog()  # __init__ no longer raises

    if log_service._collection is None:
        print(
            "Failed to initialize ConversationLog: "
            "MongoDB connection failed during init."
        )
        print("Please ensure your local MongoDB instance is running.")
        exit(1)

    # Clean up previous test data if it exists for a fresh run
    # This is useful for development but should be handled carefully in production.
    print("\n--- Cleaning up previous test data ---")
    log_service._collection.delete_many({})  # Clear the collection
    print("Collection cleared.")

    # Create dummy data
    test_user_id_1 = uuid4()
    test_user_id_2 = uuid4()
    test_conversation_id_1 = uuid4()
    test_conversation_id_2 = uuid4()

    print("\n--- Logging Turns ---")
    # Turn 1: User 1, Conv 1
    turn1 = ConversationTurn(
        turn_id=uuid4(),
        conversation_id=test_conversation_id_1,
        user_id=test_user_id_1,
        timestamp=datetime.now(UTC),
        speaker="user",
        text="Hello Viki!",
    )
    result1 = log_service.log_turn(turn1)
    print(f"Log Turn 1 Result: {result1}")
    time.sleep(0.01)  # Ensure distinct timestamps

    # Turn 2: User 1, Conv 1
    turn2 = ConversationTurn(
        turn_id=uuid4(),
        conversation_id=test_conversation_id_1,
        user_id=test_user_id_1,
        timestamp=datetime.now(UTC),
        speaker="viki",
        text="I'm doing great, thank you! How can I assist you today?",
    )
    result2 = log_service.log_turn(turn2)
    print(f"Log Turn 2 Result: {result2}")
    time.sleep(0.01)

    # Turn 3: User 1, Conv 1
    turn3 = ConversationTurn(
        turn_id=uuid4(),
        conversation_id=test_conversation_id_1,
        user_id=test_user_id_1,
        timestamp=datetime.now(UTC),
        speaker="user",
        text="What's the weather like?",
    )
    result3 = log_service.log_turn(turn3)
    print(f"Log Turn 3 Result: {result3}")
    time.sleep(0.01)

    # Turn 4: User 1, Conv 2 (New conversation for same user)
    turn4 = ConversationTurn(
        turn_id=uuid4(),
        conversation_id=test_conversation_id_2,
        user_id=test_user_id_1,
        timestamp=datetime.now(UTC),
        speaker="user",
        text="Let's talk about something else. Tell me a joke.",
    )
    result4 = log_service.log_turn(turn4)
    print(f"Log Turn 4 Result: {result4}")
    time.sleep(0.01)

    # Turn 5: User 2, Conv 3 (New user, new conversation)
    turn5 = ConversationTurn(
        turn_id=uuid4(),
        conversation_id=uuid4(),
        user_id=test_user_id_2,
        timestamp=datetime.now(UTC),
        speaker="user",
        text="Hello Viki, are you there?",
    )
    result5 = log_service.log_turn(turn5)
    print(f"Log Turn 5 Result: {result5}")
    time.sleep(0.01)

    print(
        "\n--- Retrieving Turns for a specific Conversation "
        "(test_conversation_id_1) ---"
    )
    retrieved_conv_turns = log_service.get_conversation_turns(test_conversation_id_1)
    if retrieved_conv_turns["success"]:
        print(f"Found {len(retrieved_conv_turns['history'])} turns for Conv1:")
        for turn in retrieved_conv_turns["history"]:
            print(f"- {turn.timestamp} [{turn.speaker}]: {turn.text}")
    else:
        print(
            f"Error retrieving conversation turns: "
            f"{retrieved_conv_turns['error']['message']}"
        )

    print("\n--- Retrieving Recent Turns for a User (test_user_id_1) with limit 2 ---")
    recent_user_turns = log_service.get_recent_user_turns(test_user_id_1, limit=2)
    if recent_user_turns["success"]:
        print(f"Found {len(recent_user_turns['history'])} recent turns for user 1:")
        for turn in recent_user_turns["history"]:
            print(f"- {turn.timestamp} [{turn.speaker}]: {turn.text}")
    else:
        print(
            f"Error retrieving recent user turns: "
            f"{recent_user_turns['error']['message']}"
        )

    print(
        "\n--- Retrieving Turns with Timestamp Range "
        "(approx last 0.1 sec) from Conv1 ---"
    )
    # Adjust time range based on your execution speed and desired specificity
    end_time_range = datetime.now(UTC)
    start_time_range = end_time_range - timedelta(seconds=0.1)

    retrieved_range_turns = log_service.get_conversation_turns(
        test_conversation_id_1,
        from_timestamp=start_time_range,
        to_timestamp=end_time_range,
    )
    if retrieved_range_turns["success"]:
        print(
            f"Found {len(retrieved_range_turns['history'])} turns in range for Conv1:"
        )
        for turn in retrieved_range_turns["history"]:
            print(f"- {turn.timestamp} [{turn.speaker}]: {turn.text}")
    else:
        print(
            f"Error retrieving turns by range: "
            f"{retrieved_range_turns['error']['message']}"
        )

    print("\n--- Attempting to retrieve for non-existent conversation ---")
    non_existent_conv_turns = log_service.get_conversation_turns(uuid4())
    print(
        f"Result for non-existent conv (success: "
        f"{non_existent_conv_turns['success']}, "
        f"history_count: {len(non_existent_conv_turns['history'])})"
    )
    assert len(non_existent_conv_turns["history"]) == 0

    print("\n--- Attempting to retrieve for non-existent user ---")
    non_existent_user_turns = log_service.get_recent_user_turns(uuid4())
    print(
        f"Result for non-existent user (success: "
        f"{non_existent_user_turns['success']}, "
        f"history_count: {len(non_existent_user_turns['history'])})"
    )
    assert len(non_existent_user_turns["history"]) == 0

    print("\n--- Demonstration complete ---")
    if log_service._client is not None:
        log_service._client.close()  # Close MongoDB connection
        print("MongoDB connection closed.")
    else:
        print("MongoDB client not available to close.")
