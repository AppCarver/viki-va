"""The core Language Center for Viki Virtual Assistant.

This module defines the `LanguageCenter` class, which acts as the central
orchestrator for all natural language processing functionalities within Viki's
'brain'. It encapsulates both Natural Language Understanding (NLU) and
Natural Language Generation (NLG) services.

The `LanguageCenter` provides a unified interface for other brain components
(like `InputProcessor` and `PreFrontalCortex`) to interact with language
processing capabilities without needing to know the specific NLU or NLG
implementations (e.g., Gemini, OpenAI, custom models).

Responsibilities include:
- Initializing and managing instances of `NLUServiceInterface` and `NLGServiceInterface`
- Providing a high-level `understand_user_input` method that delegates to the NLU srvc.
- Providing a high-level `generate_response` method that delegates to the NLG service.
- Optionally, handling the fetching of `ConversationContext` if NLU/NLG require it,
  and passing it to the respective services.
"""

from typing import Any

from services.brain.language_center.nlg.src.nlg_service_interface import (
    NLGServiceInterface,
)
from services.brain.language_center.nlu.src.nlu_service_interface import (
    NLUServiceInterface,
)

# Placeholder for ShortTermMemoryService, if LanguageCenter is responsible
# for fetching context
# from services.brain.short_term_mem.src.short_term_memory_service import (
# ShortTermMemoryService)


class LanguageCenter:
    """Manages Natural Language Understanding (NLU) and Generation (NLG) for Viki."""

    def __init__(
        self,
        nlu_service: NLUServiceInterface,
        nlg_service: NLGServiceInterface,
        # short_term_memory_service:
        #   Optional[ShortTermMemoryService] = None
        # Optional: if context fetching is here
    ) -> None:
        """Initialize the LanguageCenter with NLU and NLG service implementations.

        Args:
        ----
            nlu_service: An instance of a class implementing NLUServiceInterface,
                         responsible for understanding user input.
            nlg_service: An instance of a class implementing NLGServiceInterface,
                         responsible for generating Viki's responses.
            short_term_memory_service:
                Optional service to retrieve conversation context.

        """
        self.nlu_service = nlu_service
        self.nlg_service = nlg_service
        # self.short_term_memory_service = short_term_memory_service
        # print("LanguageCenter initialized with NLU and NLG services.")

    def understand_user_input(
        self, text: str, conversation_id: str, user_id: str
    ) -> dict[str, Any]:
        """Process user input using the configured NLU service.

        Args:
        ----
            text: The raw text input from the user.
            conversation_id: The ID of the current conversation.
            user_id: The ID of the user.

        Returns
        -------
            A dictionary containing the NLU result (intent, entities, confidence, etc.).

        """
        # In a real scenario, we might fetch context here and pass it to NLU
        # For now, NLU only uses 'text' as per your GeminiNLUService
        # If the NLU service needs context, we would fetch it here:
        # context = self.short_term_memory_service.get_context_for_nlu(
        #   conversation_id, user_id)
        # return self.nlu_service.process_nlu(text, context)
        return self.nlu_service.process_nlu(text)

    def generate_response(
        self,
        dialogue_act: str,
        response_content: dict[str, Any],
        conversation_id: str,
        user_id: str,
    ) -> dict[str, str]:
        """Generate a natural language response using the configured NLG service.

        Args:
        ----
            dialogue_act: The high-level intent or action for Viki's response.
            response_content: Structured data to be incorporated into the response.
            conversation_id: The ID of the current conversation (for context retrieval).
            user_id: The ID of the user (for context retrieval).

        Returns
        -------
            A dictionary containing the generated text, e.g., {"generated_text": "..."}.

        """
        # This is where you would fetch conversation context for NLG if needed.
        # For initial implementation, we can pass an empty dictionary for context.
        # if self.short_term_memory_service:
        #     conversation_context = self.short_term_memory_service.get_context_for_nlg(
        #           conversation_id, user_id)
        # else:
        #     conversation_context = {}
        conversation_context: dict[str, Any] = {}  # Placeholder for now

        return self.nlg_service.generate_response(
            dialogue_act=dialogue_act,
            response_content=response_content,
            conversation_context=conversation_context,
        )
