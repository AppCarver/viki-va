"""LongTermMemory component for Viki.

This module implements the LongTermMemoryInterface, providing functionalities
for storing, retrieving, updating, and deleting facts using a local JSON file
for persistence.
"""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from services.brain.long_term_mem.src.long_term_memory_interface import (
    LongTermMemoryInterface,
)
from shared_libs.errors.errors import LongTermMemoryError


class LongTermMemory(LongTermMemoryInterface):
    """Manage Viki's LTM storing and retrieving facts from a JSON file."""

    def __init__(self, file_path: str) -> None:
        """Initialize the LongTermMemory component.

        Args:
        ----
            file_path (str): The path to the JSON file used for memory
                persistence.

        """
        self.file_path = file_path
        self._memory: dict[str, dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        self._load_memory()
        self.logger.info(f"LongTermMemory initialized, loaded from {self.file_path}.")

    def _load_memory(self) -> None:
        """Load the memory from the specified JSON file.

        If the file does not exist or is empty, initializes an empty memory.
        Handles JSON decoding errors and I/O errors gracefully.
        """
        if not os.path.exists(self.file_path) or os.stat(self.file_path).st_size == 0:
            self.logger.info(
                f"No existing memory file found at {self.file_path} or file "
                "is empty. Initialize empty memory."
            )
            self._memory = {}
            return

        try:
            with open(self.file_path, encoding="utf-8") as f:
                self._memory = json.load(f)
            self.logger.info(f"Successfully loaded memory from {self.file_path}.")
        except json.JSONDecodeError as e:
            self.logger.error(
                f"Error decoding JSON from {self.file_path}: {e}. "
                "Initialize empty memory.",
                exc_info=True,
            )
            self._memory = {}
        except OSError as e:
            self.logger.error(
                f"I/O error loading memory from {self.file_path}: {e}. "
                "Initialize empty memory.",
                exc_info=True,
            )
            self._memory = {}
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred while loading memory from "
                f"{self.file_path}: {e}. Initialize empty memory.",
                exc_info=True,
            )
            self._memory = {}

    def _save_memory(self) -> None:
        """Save the current memory to the specified JSON file.

        Creates the directory if it does not exist.
        Raises LongTermMemoryError on I/O or unexpected errors.
        """
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._memory, f, indent=4)
            self.logger.info(f"Successfully saved memory to {self.file_path}.")
        except OSError as e:
            self.logger.error(f"I/O error saving memory to {self.file_path}: {e}")
            raise LongTermMemoryError(
                f"Failed to save memory due to I/O error: {e}"
            ) from e
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred while saving memory to "
                f"{self.file_path}: {e}",
                exc_info=True,
            )
            raise LongTermMemoryError(
                f"Failed to save memory due to unexpected error: {e}"
            ) from e

    def store_fact(
        self,
        user_id: UUID,
        fact_data: dict[str, Any],
        retention_policy: str | None = None,
    ) -> dict[str, Any]:
        """Store a new fact or piece of information in long-term memory.

        Args:
        ----
            user_id (UUID): The ID of the user associated with the fact.
            fact_data (Dict[str, Any]): A dictionary containing the fact's details.
            retention_policy (Optional[str]): Defines how long this fact should
                be retained. Defaults to "permanent".

        Returns:
        -------
            Dict[str, Any]: A dictionary indicating success and optionally a
                fact_id.
                            Example: {"success": True, "fact_id": "UUID",
                                      "error": None}

        """
        try:
            fact_id = uuid4()
            user_id_str = str(user_id)
            fact_id_str = str(fact_id)
            timestamp = datetime.now(UTC).isoformat()

            if user_id_str not in self._memory:
                self._memory[user_id_str] = {}

            # Add internal metadata to fact_data
            stored_fact_data = {
                "fact_id": fact_id_str,
                "user_id": user_id_str,
                "timestamp": timestamp,
                "retention_policy": (
                    retention_policy if retention_policy is not None else "permanent"
                ),
                **fact_data,  # Merge incoming fact_data last to allow it to
                # override metadata if present
            }

            self._memory[user_id_str][fact_id_str] = stored_fact_data
            self._save_memory()
            self.logger.info(f"Fact '{fact_id_str}' stored for user '{user_id_str}'.")
            return {"success": True, "fact_id": fact_id, "error": None}
        except LongTermMemoryError as e:
            self.logger.error(
                f"Failed to store fact for user '{user_id}': {e}", exc_info=True
            )
            return {
                "success": False,
                "fact_id": None,
                "error": {"code": "PERSISTENCE_ERROR", "message": str(e)},
            }
        except Exception as e:
            self.logger.exception(
                f"An unexpected error occurred while storing fact for user '{user_id}'."
            )
            return {
                "success": False,
                "fact_id": None,
                "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
            }

    def retrieve_facts(
        self,
        user_id: UUID | None = None,
        query_criteria: dict[str, Any] | None = None,
        limit: int | None = None,
        semantic_query: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve facts from long-term memory based on provided criteria.

        Args:
        ----
            user_id (Optional[UUID]): Filter facts by a specific user.
            query_criteria (Optional[Dict[str, Any]]): A dictionary specifying
                conditions for retrieval (e.g., {'type': 'preference'}).
            limit (Optional[int]): Maximum number of facts to retrieve.
            semantic_query (Optional[str]): Natural language query for
                semantic search (Future).

        Returns:
        -------
            Dict[str, Any]: A dictionary containing a list of fact_data
                dictionaries.
                            Example: {"success": True, "facts": [{}],
                                      "error": None}

        """
        found_facts: list[dict[str, Any]] = []
        try:
            # Handle semantic_query as not implemented for now
            if semantic_query:
                self.logger.warning(
                    "Semantic query feature is not yet implemented. "
                    f"Ignoring semantic_query: '{semantic_query}'."
                )
                # For now, if semantic_query is provided, we return an empty list
                # as we don't have a semantic search engine integrated.
                return {"success": True, "facts": [], "error": None}

            target_user_ids = [str(user_id)] if user_id else list(self._memory.keys())

            for current_user_id in target_user_ids:
                if current_user_id not in self._memory:
                    continue  # Skip if user_id doesn't exist in memory

                for _fact_id, fact in self._memory[current_user_id].items():
                    # Apply query_criteria filtering
                    if query_criteria:
                        match = True
                        for key, value in query_criteria.items():
                            if key not in fact or fact[key] != value:
                                match = False
                                break
                        if not match:
                            continue

                    found_facts.append(fact)

                    # Apply limit
                    if limit is not None and len(found_facts) >= limit:
                        break  # Break from inner loop (facts for current user)

                if limit is not None and len(found_facts) >= limit:
                    break  # Break from outer loop (users)

            self.logger.info(
                f"Retrieved {len(found_facts)} facts for user(s) "
                f"'{user_id}' with criteria '{query_criteria}'."
            )
            return {"success": True, "facts": found_facts, "error": None}
        except Exception as e:
            self.logger.exception(
                f"An unexpected error occurred while retrieving facts for user "
                f"'{user_id}' with criteria '{query_criteria}'."
            )
            return {
                "success": False,
                "facts": [],
                "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
            }

    def update_fact(
        self, fact_id: UUID, updated_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing fact in long-term memory.

        Args:
        ----
            fact_id (UUID): The unique identifier of the fact to update.
            updated_data (dict[str, Any]): Dictionary containing fields to update.

        Returns:
        -------
            dict[str, Any]: A dictionary indicating success.
                            Example: {"success": True, "error": None}

        """
        try:
            fact_id_str = str(fact_id)
            found = False
            for user_id_str in self._memory:
                if fact_id_str in self._memory[user_id_str]:
                    # Update only specified fields, keep existing ones
                    self._memory[user_id_str][fact_id_str].update(updated_data)
                    found = True
                    break

            if found:
                self._save_memory()
                self.logger.info(f"Fact '{fact_id_str}' updated successfully.")
                return {"success": True, "error": None}
            else:
                self.logger.warning(
                    f"Fact with ID '{fact_id_str}' not found for update."
                )
                return {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Fact with ID '{fact_id_str}' not found.",
                    },
                }
        except LongTermMemoryError as e:
            self.logger.error(f"Failed to update fact '{fact_id}': {e}")
            return {
                "success": False,
                "error": {"code": "PERSISTENCE_ERROR", "message": str(e)},
            }
        except Exception as e:
            self.logger.exception(
                f"An unexpected error occurred while updating fact '{fact_id}'."
            )
            return {
                "success": False,
                "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
            }

    def delete_fact(self, fact_id: UUID) -> dict[str, Any]:
        """Delete a fact from long-term memory.

        Args:
        ----
            fact_id (UUID): The unique identifier of the fact to delete.

        Returns:
        -------
            dict[str, Any]: A dictionary indicating success.
                            Example: {"success": True, "error": None}

        """
        try:
            fact_id_str = str(fact_id)
            found = False
            for user_id_str in self._memory:
                if fact_id_str in self._memory[user_id_str]:
                    del self._memory[user_id_str][fact_id_str]
                    found = True
                    # Clean up empty user entries
                    if not self._memory[user_id_str]:
                        del self._memory[user_id_str]
                    break

            if found:
                self._save_memory()
                self.logger.info(f"Fact '{fact_id_str}' deleted successfully.")
                return {"success": True, "error": None}
            else:
                self.logger.warning(
                    f"Fact with ID '{fact_id_str}' not found for deletion."
                )
                return {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Fact with ID '{fact_id_str}' not found.",
                    },
                }
        except LongTermMemoryError as e:
            self.logger.error(f"Failed to delete fact '{fact_id}': {e}")
            return {
                "success": False,
                "error": {"code": "PERSISTENCE_ERROR", "message": str(e)},
            }
        except Exception as e:
            self.logger.exception(
                f"An unexpected error occurred while deleting fact '{fact_id}'."
            )
            return {
                "success": False,
                "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
            }
