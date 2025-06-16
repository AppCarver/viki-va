# services/nlu_service/nlu_service_interface.py
"""Defines the abstract interface for Natural Language Understanding (NLU) services.

This module provides the `NLUServiceInterface` Abstract Base Class (ABC),
which sets the contract for any NLU provider (e.g., Gemini, OpenAI, custom models)
used within the Viki Virtual Assistant system. By implementing this interface,
different NLU services can be seamlessly integrated and swapped, ensuring
the `InputProcessor` remains independent of specific LLM technologies.

"""

from abc import ABC, abstractmethod


class NLUServiceInterface(ABC):
    """Abstract Base Class (ABC).

    Defining the interface for any NLU (Natural Language Understanding) service.

    Any class that processes text input to extract intent and entities must implement
    this interface.

    This ensures that the InputProcessor remains agnostic to the specific NLU provider.
    """

    @abstractmethod
    def process_nlu(self, text: str) -> dict:
        """Process the given text input.

        Use the NLU service to extract intent and entities.

        Args:
        ----
            text: The user's input text to be processed.

        Returns
        -------
            A dictionary containing the extracted intent and entities,
            e.g., {"intent": "greet", "entities": {"name": "Viki"}}.
            The structure should be consistent across all implementations.
            If no clear intent is found, it should return
                {"intent": "unknown", "entities": {"raw_query": text}}.

        Raises
        ------
            NLUProcessingError: If there's an error during NLU processing
            (e.g., API issues, invalid response).

        """
        pass  # Abstract methods do not contain an implementation
