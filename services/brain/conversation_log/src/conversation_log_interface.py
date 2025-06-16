"""Define the abstract interface for Viki's Conversation Log component.

This interface establishes the contract for all ConversationLog implementations,
ensuring that other Viki brain components can interact with the Conversation Log
service in a loosely coupled manner, regardless of the underlying storage
mechanism.
"""

import abc
from datetime import datetime
from typing import Any
from uuid import UUID


# Conceptual Data Model for a Conversation Turn
# In a real scenario, this might be a more complex Pydantic model
# or a dataclass, potentially defined in a data_models directory.
class ConversationTurn:
    """Represents a single turn in a conversation."""

    def __init__(
        self,
        turn_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        timestamp: datetime,
        speaker: str,  # "user" or "viki"
        text: str,
        nlu_data: dict[str, Any] | None = None,
        nlg_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a ConversationTurn.

        Args:
        ----
            turn_id (UUID): Unique identifier for this turn.
            conversation_id (UUID): Identifier for the conversation this turn
                                    belongs to.
            user_id (UUID): Identifier for the user involved in this turn.
            timestamp (datetime): UTC timestamp of when the turn occurred.
            speaker (str): Indicates who made the utterance ("user" or "viki").
            text (str): The actual text content of the turn.
            nlu_data (Optional[Dict[str, Any]]): NLU processing results for
                                                  the turn.
            nlg_data (Optional[Dict[str, Any]]): NLG generation data for the turn.
            metadata (Optional[Dict[str, Any]]): Additional arbitrary metadata.

        """
        self.turn_id = turn_id
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.timestamp = timestamp
        self.speaker = speaker
        self.text = text
        self.nlu_data = nlu_data if nlu_data is not None else {}
        self.nlg_data = nlg_data if nlg_data is not None else {}
        self.metadata = metadata if metadata is not None else {}

    def to_dict(self) -> dict[str, Any]:
        """Convert the ConversationTurn object to a dictionary for storage.

        Timestamps are converted to ISO 8601 strings for consistent storage
        and retrieval.
        """
        return {
            "turn_id": str(self.turn_id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "timestamp": self.timestamp.isoformat(),  # Convert to ISO string
            "speaker": self.speaker,
            "text": self.text,
            "nlu_data": self.nlu_data,
            "nlg_data": self.nlg_data,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ConversationTurn":
        """Create a ConversationTurn object from a dictionary.

        Expects the 'timestamp' field to be an ISO 8601 formatted string.
        """
        return ConversationTurn(
            turn_id=UUID(data["turn_id"]),
            conversation_id=UUID(data["conversation_id"]),
            user_id=UUID(data["user_id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            speaker=data["speaker"],
            text=data["text"],
            nlu_data=data.get("nlu_data"),
            nlg_data=data.get("nlg_data"),
            metadata=data.get("metadata"),
        )


class ConversationLogInterface(abc.ABC):
    """Abstract Base Class for the ConversationLog component.

    Defines the contract for Viki's conversation logging operations, ensuring
    loose coupling between components that interact with the conversation history
    and the underlying storage implementation.
    """

    @abc.abstractmethod
    def log_turn(self, turn: ConversationTurn) -> dict[str, Any]:
        """Store a new conversation turn record.

        Args:
        ----
            turn (ConversationTurn): A fully formed ConversationTurn object.

        Returns
        -------
            Dict[str, Any]: A dictionary indicating success and the turn_id.
                            Example: {"success": True, "turn_id": "UUID",
                                      "error": None}

        """
        pass

    @abc.abstractmethod
    def get_conversation_turns(
        self,
        conversation_id: UUID,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Retrieve a sequence of ConversationTurn records for a specific conversation.

        Args:
        ----
            conversation_id (UUID): The ID of the conversation.
            from_timestamp (Optional[datetime]): Start timestamp for filtering.
            to_timestamp (Optional[datetime]): End timestamp for filtering.
            limit (Optional[int]): Maximum number of turns to retrieve.
            offset (Optional[int]): Number of turns to skip from the beginning.

        Returns
        -------
            Dict[str, Any]: A dictionary containing a list of ConversationTurn
                            objects. Example: {"success": True,
                            "history": [turn1, turn2], "error": None}

        """
        pass

    @abc.abstractmethod
    def get_recent_user_turns(
        self, user_id: UUID, limit: int | None = None
    ) -> dict[str, Any]:
        """Retrieve the most recent ConversationTurns.

        Across all conversations for a given user.

        Args:
        ----
            user_id (UUID): The ID of the user.
            limit (Optional[int]): Maximum number of recent turns to retrieve.

        Returns
        -------
            Dict[str, Any]: A dictionary containing a list of ConversationTurn
                            objects. Example: {"success": True,
                            "history": [turn1, turn2], "error": None}

        """
        pass
