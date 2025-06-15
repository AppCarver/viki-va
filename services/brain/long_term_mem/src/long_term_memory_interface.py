"""Define the abstract interface for Viki's Long-Term Memory (LTM) component.

This interface establishes the contract for all LTM implementations, ensuring
that other Viki brain components can interact with the LTM service in a
loosely coupled manner, regardless of the underlying storage mechanism.
"""

import abc
from typing import Any
from uuid import UUID


class LongTermMemoryInterface(abc.ABC):
    """Abstract Base Class for the LongTermMemory component.

    Defines the contract for Viki's long-term memory operations, ensuring loose
    coupling between components that interact with persistent knowledge and
    the underlying storage implementation.
    """

    @abc.abstractmethod
    def store_fact(
        self,
        user_id: UUID,
        fact_data: dict[str, Any],
        retention_policy: str | None = None,
    ) -> dict[str, Any]:
        """Store a new fact or piece of information in long-term memory.

        Args:
            user_id (UUID):
                The ID of the user associated with the fact (if user-specific).
            fact_data (Dict[str, Any]):
                A dictionary containing the fact's details.
                Expected to conform to a LongTermFact data model schema.
            retention_policy (Optional[str]):
                Defines how long this fact should be retained
                (e.g., "permanent", "temporary", "decaying").
            Defaults to "permanent" for user preferences.

        Returns:
            Dict[str, Any]: A dictionary indicating success and optionally a fact_id.
                            Example: {"success": True, "fact_id": "UUID", "error": None}

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def retrieve_facts(
        self,
        user_id: UUID | None = None,
        query_criteria: dict[str, Any] | None = None,
        limit: int | None = None,
        semantic_query: str | None = None,  # Future: for semantic search
    ) -> dict[str, Any]:
        """Retrieve facts from long-term memory based on provided criteria.

        Args:
            user_id (Optional[UUID]): Filter facts by a specific user.
            query_criteria (Optional[Dict[str, Any]]):
                A dictionary specifying conditions
                for retrieval (e.g., {'type': 'preference'}).
            limit (Optional[int]): Maximum number of facts to retrieve.
            semantic_query (Optional[str]):
                Natural language query for semantic search (Future).

        Returns:
        -------
            Dict[str, Any]: A dictionary containing a list of fact_data dictionaries.
                            Example: {"success": True, "facts": [{}], "error": None}

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def update_fact(
        self, fact_id: UUID, updated_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing fact in long-term memory.

        Args:
            fact_id (UUID): The unique identifier of the fact to update.
            updated_data (Dict[str, Any]): Dictionary containing fields to update.

        Returns:
        -------
            Dict[str, Any]: A dictionary indicating success.
                            Example: {"success": True, "error": None}

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_fact(self, fact_id: UUID) -> dict[str, Any]:
        """Delete a fact from long-term memory.

        Args:
            fact_id (UUID): The unique identifier of the fact to delete.

        Returns:
            Dict[str, Any]: A dictionary indicating success.
                            Example: {"success": True, "error": None}

        """
        raise NotImplementedError()
