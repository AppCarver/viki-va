# services/brain.language_center.nlg_service_interface.py
"""Defines the abstract interface for Natural Language Generation (NLG) services.

This module provides the `NLGServiceInterface` Abstract Base Class (ABC),
which sets the contract for any NLG provider (e.g., Gemini, OpenAI, custom models)
used within the Viki Virtual Assistant system. By implementing this interface,
different NLG services can be seamlessly integrated and swapped, ensuring
the `InputProcessor` remains independent of specific LLM technologies.

"""

from abc import ABC, abstractmethod
from typing import Any


class NLGServiceInterface(ABC):
    """Abstract Base Class (ABC) defines the interface for any NLG service.

    Any class responsible forconverting structured data (dialog act, response content)
    into natural language test must implement this interface.

    This ensures the language_center remains agnostic to the specific NLG provider.
    """

    @abstractmethod
    def generate_response(
        self,
        dialogue_act: str,
        response_content: dict[str, Any],
        conversation_context: dict[str, Any],
    ) -> dict[str, str]:
        """Generate an NL response based on the dialogue act and content.

        Args:
        ----
            dialogue_act (str): The high-level intent or ation VIKI needs to preform.
            response_content (dict[str, Any]): A dictionary containing key-value
                pairs of data needed to form the response
                (e.g., {"city": "London", "temperature": "20C"}).
            conversation_context (dict[str, Any]): A dictionary representing relevant
                parts of the ongoing conversation context, such as user preferences,
                previous turns, active goals, etc.

        Returns
        -------
            dict[str, str]:  A dictionary containing the generated text, e.g.,
                {"generated_text": "The weather in London is 20 degrees Celsius."}.
                If generation fails or results in an empty response, it should ideally
                return {"generated_text": "I'm sorry, I couldn't generate a response
                for that."} or raise an appropriate error.

        Raises
        ------
            NLGGenerationError: If there's an error during NLG processing
            (e.g., API issues, invalid response).

        """
        pass
