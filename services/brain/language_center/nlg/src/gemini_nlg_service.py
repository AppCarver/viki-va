"""Gemini NLG Service Implementation for Viki Virtual Assistant.

This module provides a concrete implementation of the `NLGServiceInterface`
using Google's Gen AI SDK for Natural Language Generation (NLG).

The `GeminiNLGService` class is responsible for:
- Initializing the Google Gen AI `Client` object and configuring the API key
  (via GOOGLE_API_KEY environment variable).
- Holding the specific NLG prompt template optimized for Gemini models,
  which guides the model in generating natural language responses.
- Sending structured input (dialogue act, response content, conversation context)
  to the configured Gemini model (e.g., `gemini-pro`) via
  `client.models.generate_content`.
- Performing basic parsing and validation of the text response received from the
  Gemini API.
- Handling API-related errors and empty responses by raising `NLGGenerationError`.

This service encapsulates all Gemini-specific logic for NLG, ensuring that the
`language_center` component (and other parts of Viki that rely on NLG) remains
decoupled from the underlying LLM provider. This allows for easy swapping or
addition of other NLG services (e.g., OpenAI, custom models) by simply
implementing the `NLGServiceInterface`.

Dependencies:
- `google-genai` (Installed via `pip install google-genai`)

Raises:
    ValueError:
        If the GOOGLE_API_KEY environment variable is not set during initialization.
    NLGGenerationError: For any issues encountered during the NLG processing
                        via the Gemini API, including API errors, network issues,
                        or malformed/missing data in the Gemini response.

"""

import json
import os
from typing import Any

from google import genai

from services.brain.language_center.nlg.src.nlg_service_interface import (
    NLGServiceInterface,
)
from shared_libs.errors.errors import NLGGenerationError


class GeminiNLGService(NLGServiceInterface):
    """Implements NLGServiceInterface using Google's Gen AI SDK for NLG."""

    # This prompt is crucial. We'll refine this.
    NLG_PROMPT_TEMPLATE = """
    You are Viki, a helpful and friendly virtual assistant.
    Generate a natural language response based on the following `dialogue_act`,
    `response_content`, and `conversation_context`.
    Be concise, natural, and helpful. Do not add conversational filler unless
    explicitly requested.

    `Dialogue Act`: {dialogue_act}
    `Response Content`: {response_content}
    `Conversation Context`: {conversation_context}

    ---
    Examples:
    `Dialogue Act`: inform_weather
    `Response Content`: {{"city": "London", "temperature": "20C"}}
    `Conversation Context`: {{}}
    `Response`: The current temperature in London is 20 degrees Celsius.

    `Dialogue Act`: confirm_booking
    `Response Content`: {{"item": "pizza", "time": "7 PM"}}
    `Conversation Context`: {{}}
    `Response`: Got it! Your pizza order is confirmed for 7 PM.

    `Dialogue Act`: ask_for_clarification
    `Response Content`: {{"missing_info": "time"}}
    `Conversation Context`: {{}}
    `Response`: I need to know the time. Could you please specify?

    `Dialogue Act`: greet
    `Response Content`: {{}}
    `Conversation Context`: {{"user_name": "Alex"}}
    `Response`: Hello Alex! How can I help you today?

    `Dialogue Act`: farewell
    `Response Content`: {{}}
    `Conversation Context`: {{}}
    `Response`: Goodbye! Have a great day.

    ---
    Generated Response:
    """

    def __init__(self, model_name: str = "gemini-pro") -> None:
        """Initialize the GeminiNLGService using the Google Gen AI SDK client.

        This constructor sets up the connection to the Gemini API by
        initializing the client and specifying the model to be used for NLG.
        It also ensures that the necessary API key is available in the environment.

        Args:
            model_name (str, optional): The name of the Gemini model to use for NLG
                                        (e.g., "gemini-pro"). Defaults to "gemini-pro".

        Raises:
            ValueError: If the `GOOGLE_API_KEY` environment variable is not set,
                        which is required to authenticate with the Gemini API.

        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set for GeminiNLGService."
            )
        self.client = genai.Client()
        self.model_name = model_name
        print(f"GeminiNLGService initialized with model: {self.model_name}")

    def generate_response(
        self,
        dialogue_act: str,
        response_content: dict[str, Any],
        conversation_context: dict[str, Any],
    ) -> dict[str, str]:
        """Generate a natural language response using the Gemini API."""
        # Format the prompt using the provided data
        prompt = self.NLG_PROMPT_TEMPLATE.format(
            dialogue_act=dialogue_act,
            response_content=json.dumps(response_content),  # JSON dump dicts for prompt
            conversation_context=json.dumps(conversation_context),
        )

        try:
            # Call the Gemini API
            response = self.client.models.generate_content(
                model=self.model_name, contents=[prompt]
            )

            generated_text = response.text
            if generated_text is None:
                raise NLGGenerationError(
                    "Gemini API returned an empty response (None) for NLG."
                )

            # Basic cleanup: remove leading/trailing whitespace
            clean_text = generated_text.strip()

            # Add any specific post-processing here if Gemini adds unwanted
            # prefixes/suffixes. For example, if it puts "Response: " at the beginning:
            if clean_text.startswith("Response: "):
                clean_text = clean_text.removeprefix("Response: ").strip()

            if not clean_text:
                raise NLGGenerationError(
                    "Generated response text was empty or consisted only of"
                    " whitespace after processing."
                )

            return {"generated_text": clean_text}

        except Exception as e:
            raise NLGGenerationError(f"Gemini API call for NLG failed: {e}") from e
