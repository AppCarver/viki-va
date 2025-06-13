# services/nlu_service/src/gemini_nlu_service.py

"""Gemini NLU Service Implementation for Viki Virtual Assistant.

(using the NEW Google Gen AI SDK)

This module provides a concrete implementation of the `NLUServiceInterface`
using Google's latest Gen AI SDK for Natural Language Understanding (NLU).

The `GeminiNLUService` class is responsible for:
- Initializing the new Google Gen AI `Client` object and configuring the API key
  (via GOOGLE_API_KEY environment variable).
- Holding the specific NLU prompt template optimized for Gemini models.
- Sending user input text to the configured Gemini model (e.g., `gemini-pro`).
  Calls are made through the `client.models.generate_content` method.
- Parsing and validating the JSON response received from the Gemini API.
- Extracting the determined user intent and relevant entities.
- Handling API-related errors, JSON parsing failures, and invalid responses
  by raising `NLUProcessingError`.

This service encapsulates all Gemini-specific logic, ensuring that the
`InputProcessor` (and other components that rely on NLU) remains
decoupled from the underlying LLM provider. This allows for easy
swapping or addition of other NLU services (e.g., OpenAI, custom models)
by simply implementing the `NLUServiceInterface`.

Dependencies:
- `google-genai` (The new SDK package name, installed via
  `pip install google-genai`)

Raises
------
    ValueError:
        If the GOOGLE_API_KEY environment variable is not set during
        initialization.
    NLUProcessingError: For any issues encountered during the NLU processing
                        via the Gemini API, including API errors, network issues,
                        or malformed/missing data in the Gemini response.

"""

import json
import os
from typing import Any  # Added Optional for type hinting

from google import genai
from google.genai import types

from services.brain.language_center.nlu.src.nlu_service_interface import (
    NLUServiceInterface,
)

# Import NLUProcessingError from where it's currently defined
from services.input_processor.src.input_processor import NLUProcessingError


class GeminiNLUService(NLUServiceInterface):
    """Implement NLUServiceInterface.

    Uses Google's NEW Gen AI SDK for Natural Language Understanding (NLU).

    """

    # Define the UNKNOWN_INTENT_NAME constant here,
    # specific to this implementation.
    # It aligns with the "unknown" intent string
    # expected by the interface's contract.
    UNKNOWN_INTENT_NAME: str = "unknown"

    # The NLU prompt template specific to Gemini,
    # defining how to interact with the model.
    # Note: All literal curly braces {{ and }}
    # are doubled to escape them for Python's .format() method.
    NLU_PROMPT_TEMPLATE = """
    Analyze the following user input and extract the primary intent and
    any relevant entities.

    Respond only with a JSON object. If no clear intent is found, use "unknown".
    If an intent is found but no specific entities, provide an empty
    "entities" object.

    Examples:
    Input: "Hello Viki"
    Output: {{"intent": "greet", "entities": {{}}}}

    Input: "What time is it in London?"
    Output: {{"intent": "get_time", "entities": {{"location": "London"}}}}

    Input: "Set a reminder for groceries tomorrow at 5 PM"
    Output: {{
                    "intent": "set_reminder", "entities":
                    {{"item": "groceries", "time": "tomorrow 5 PM"}}}}

    Input: "Tell me a joke"
    Output: {{"intent": "tell_joke", "entities": {{}}}}

    Input: "I need to order some pizza"
    Output: {{"intent": "order_food", "entities": {{"food_item": "pizza"}}}}

    Input: "Bye Viki"
    Output: {{"intent": "farewell", "entities": {{}}}}

    Input: "Random text that makes no sense"
    Output: {{"intent": "unknown", "entities":
                    {{"raw_query": "Random text that makes no sense"}}}}

    User Input: {text}
    """

    def __init__(self, model_name: str = "gemini-pro") -> None:  # FIX: Add -> None
        """Initialize the GeminiNLUService using the new Google Gen AI SDK client.

        Args:
        ----
            model_name: The name of the Gemini model to use (e.g., "gemini-pro").
                        It will be passed as the 'model' keyword argument.

        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set for GeminiNLUService."
            )

        # New SDK: Instantiate the client directly.
        # It picks up the API key from the env var.
        self.client = genai.Client()
        self.model_name = model_name
        print(f"GeminiNLUService initialized with model: {self.model_name}")

    def process_nlu(self, text: str) -> dict[str, Any]:
        """Process the text.

        Use the NEW Google Gen AI SDK to extract intent and entities.

        Args:
        ----
            text: The user's input text.

        Returns:
        -------
            A dictionary containing the NLU result.

        Raises:
        ------
            NLUProcessingError:
                If there's an issue with the Gemini API call or response.

        """
        prompt = self.NLU_PROMPT_TEMPLATE.format(text=text)
        print(f"Sending prompt to Gemini: {prompt}")

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", temperature=0.0
                ),
            )

            raw_gemini_response_text_or_none: str | None = response.text

            if raw_gemini_response_text_or_none is None:
                raise NLUProcessingError(
                    "Gemini API returned an empty response (None)."
                )

            # MyPy now knows raw_gemini_response_text is definitely a str here.
            raw_gemini_response_text: str = raw_gemini_response_text_or_none

            print(f"DEBUG: Raw Gemini Response Text: '{raw_gemini_response_text}'")

            # Remove Markdown code block wrappers
            clean_response_text = raw_gemini_response_text.removeprefix("```json\n")
            clean_response_text = clean_response_text.removesuffix("```\n")
            clean_response_text = clean_response_text.strip()

            # Optional fallback: If it's still wrapped (e.g., without 'json'),
            # try a generic markdown code block strip.
            if clean_response_text.startswith("```") and clean_response_text.endswith(
                "```"
            ):
                clean_response_text = clean_response_text.strip("`").strip()
            print(f"DEBUG: Cleaned Gemini Response Text: '{clean_response_text}'")

            parsed_nlu_data = json.loads(clean_response_text)

            # Validate the essential keys are present (fixed line length)
            if (
                not isinstance(parsed_nlu_data, dict)
                or "intent" not in parsed_nlu_data
                or "entities" not in parsed_nlu_data
            ):
                raise NLUProcessingError(
                    "Gemini response missing 'intent' or 'entities' keys."
                )

            # --- Extract and Process Intent/Entities ---
            intent_name: str = parsed_nlu_data.get("intent", self.UNKNOWN_INTENT_NAME)
            entities: dict[str, Any] = parsed_nlu_data.get("entities", {})

            #  -- Confidence Score Logic ---
            # Assign confidence based on wheterh the intent is identified as "unknown"
            confidence_score: float
            if intent_name == self.UNKNOWN_INTENT_NAME:
                confidence_score = 0.2  # Low confidence for unknown intents
            else:
                confidence_score = 0.95  # High confidence for recognized intents
            # End Confidence Score logic ---0

            # --- Construct the final NLU data output ---
            nlu_data_output = {
                "intent": {"name": intent_name, "confidence": confidence_score},
                "entities": entities,
                "original_text": text,
            }
            return nlu_data_output

        except json.JSONDecodeError:
            # On JSON decode error, return unknown intent with 0.0 confidence
            return {
                "intent": {"name": self.UNKNOWN_INTENT_NAME, "confidence": 0.0},
                "entities": {},
                "original_text": text,
            }
        except Exception as e:
            raise NLUProcessingError(f"Gemini API call failed: {e}") from e
