# services/input_processor/src/input_processor.py

"""InputProcessor component for the Viki Virtual Assistant.

This component is responsible for the initial processing of all user input,
whether it originates as text or audio. Its primary role is to interface
with a Natural Language Understanding (NLU) service to extract the user's
**intent** and any relevant **entities** from their query.

The InputProcessor is designed to be LLM (Large Language Model) agnostic.
It achieves this by relying on an injected `NLUServiceInterface` instance,
which abstracts away the specifics of any particular NLU provider
    (e.g., Gemini, OpenAI).
This design promotes loose coupling, extensibility, and easier testing.

Key functionalities include:
- Processing raw text input directly.
- Handling raw audio input (currently via a simulated ASR for transcription).
- Delegating NLU analysis to the configured NLU service.
- Associating device IDs with user IDs (via a placeholder method).
- Providing a structured output containing the processed text, identified intent,
  extracted entities, and relevant metadata like user/device IDs and timestamps.
- Robust error handling for NLU processing failures, invalid input,
  and unexpected issues.

Raises
------
    ValueError: If an invalid device ID format is provided during processing.
    NLUProcessingError: If the underlying NLU service encounters an error
                        during intent and entity extraction.

Returns
-------
    Dict[str, Any]: A dictionary containing the processing result, including:
        - 'success' (bool): True if NLU processed successfully (intent not 'unknown').
        - 'processed_text' (str):
            The text used for NLU.
        - 'intent' (str):
            The identified user intent (e.g., 'get_time', 'set_reminder', 'unknown').
        - 'entities' (Dict):
            A dictionary of extracted entities.
        - 'user_id' (uuid.UUID):
            The UUID associated with the user.
        - 'device_id' (str):
            The string representation of the device UUID.
        - 'timestamp' (str):
            UTC timestamp of the processing in ISO format.
        - 'message' (Optional[str]):
            A human-readable message, especially for errors.
        - 'error' (Optional[str]):
            The string representation of an encountered exception.

"""

import logging
import uuid
from datetime import datetime  # <--- FIX: Import datetime directly, remove UTC
from typing import Any  # <--- FIX: Add Dict for type hinting consistency

import pytz  # <--- FIX: Import pytz for pytz.utc

# Import the newly defined NLU Service Interface
from services.brain.language_center.nlu.src.nlu_service_interface import (
    NLUServiceInterface,
)

logger = logging.getLogger(__name__)


# Define NLUProcessingError here.
# For truly shared exceptions, consider moving this to a
# `shared_libs/exceptions.py` later.
class NLUProcessingError(Exception):
    """Create custom exception for errors during NLU processing."""

    pass


class InputProcessor:
    """InputProcessor handles the initial processing of user input.

    Regardless if it's audio or text, it aims to identify the user's intent
    and extract relevant entities from the input using an NLU service.
    """

    def __init__(
        self, nlu_service: NLUServiceInterface, asr_service: Any | None = None
    ) -> None:
        """Initialize the InputProcessor with an NLU service and optional ASR service.

        Args:
        ----
            nlu_service: An instance of a class implementing NLUServiceInterface
                         (e.g., GeminiNLUService, OpenAINLUService).
            asr_service: An optional ASR (Automatic Speech Recognition) service.
                         Currently, this is a placeholder and not fully implemented.

        """
        self.nlu_service = nlu_service
        self.asr_service = asr_service
        logger.info("InputProcessor initialized.")

    def process_text_input(self, text: str, device_id: uuid.UUID) -> dict[str, Any]:
        """Process text input, identifies intent, and extracts entities using the NLU.

        Args:
        ----
            text: The raw text input from the user.
            device_id: The UUID of the device from which the input originated.

        Returns
        -------
            A dictionary containing the processed result, including success status,
            extracted intent and entities, processed text, user_id,
            and any error message.

        """
        # Moved inside the try block so ValueError can be caught
        try:
            user_id = self._get_or_create_user_id_for_device(device_id)
            timestamp = self._get_current_utc_timestamp()

            logger.info(
                f"Processing text input from device {device_id} at {timestamp}..."
            )

            nlu_result = self._process_nlu(text)
            intent = nlu_result.get("intent", "unknown")
            entities = nlu_result.get("entities", {})

            # If the intent is unknown, include the raw query in entities
            if intent == "unknown" and "raw_query" not in entities:
                entities["raw_query"] = text

            # Acknowledge unknown intent as a successful NLU process,
            # but overall processing failed
            # for "meaningful" interaction.
            success_status = intent != "unknown"

            return {
                "success": success_status,
                "processed_text": text,
                "intent": intent,
                "entities": entities,
                "user_id": user_id,
                "device_id": str(device_id),
                "timestamp": timestamp.isoformat(),
                "message": None,
                "error": None,
            }

        except NLUProcessingError as e:
            # Handle NLU-specific errors, provide fallback for unknown intent
            error_message = f"Input processing failed due to NLU: {e}"
            logger.error("Input processing failed due to NLU: %s", e, exc_info=True)
            # Ensure user_id is set to device_id if it was valid before the NLU error
            # If the ValueError was caught, user_id would be None.
            # Here, we assume device_id was valid if we reached this point.
            try:
                # Attempt to get user_id if not set, or fall back to device_id
                # In this specific path (NLUProcessingError),
                # evice_id *should* be valid
                current_user_id = self._get_or_create_user_id_for_device(device_id)
            except ValueError:
                current_user_id = None  # Should not happen if device_id was valid

            return {
                "success": False,
                "processed_text": text,
                "intent": "unknown",  # Default to unknown on NLU processing errors
                "entities": {"raw_query": text},
                "user_id": current_user_id,  # Use the determined user_id
                "device_id": str(device_id),
                "timestamp": self._get_current_utc_timestamp().isoformat(),
                "message": error_message,
                "error": str(e),
            }
        except ValueError as e:
            # Handle validation errors (e.g., invalid device_id format)
            error_message = f"Input processing failed due to validation: {e}"
            logger.error(
                "Input processing failed due to validation: %s", e, exc_info=True
            )
            return {
                "success": False,
                "processed_text": text,
                "intent": "unknown",
                "entities": {"raw_query": text},
                "user_id": None,  # Cannot determine user_id if device_id is invalid
                "device_id": str(device_id),
                "timestamp": self._get_current_utc_timestamp().isoformat(),
                "message": error_message,
                "error": str(e),
            }
        except Exception as e:
            # Catch any other unexpected errors
            error_message = f"An unexpected error occurred during input processing: {e}"
            logger.error(
                "An unexpected error occurred during input processing: %s",
                e,
                exc_info=True,
            )
            # Attempt to get user_id if not set, or fall back to device_id
            try:
                # In this specific path (general Exception), device_id *should* be valid
                current_user_id = self._get_or_create_user_id_for_device(device_id)
            except ValueError:
                current_user_id = None  # Should not happen if device_id was valid

            return {
                "success": False,
                "processed_text": text,
                "intent": "unknown",
                "entities": {"raw_query": text},
                "user_id": current_user_id,  # Use the determined user_id
                "device_id": str(device_id),
                "timestamp": self._get_current_utc_timestamp().isoformat(),
                "message": error_message,
                "error": str(e),
            }

    def process_audio_input(
        self, raw_audio_data: bytes, device_id: uuid.UUID
    ) -> dict[str, Any]:  # <--- FIX: Use Dict
        """Process audio input. Currently uses a dummy ASR and then NLU.

        Args:
        ----
            raw_audio_data: The raw audio bytes from the user.
            device_id: The UUID of the device from which the input originated.

        Returns
        -------
            A dictionary containing the processed result, similar to process_text_input.

        """
        # --- Dummy ASR Implementation (to be replaced) ---
        # For now, we'll just simulate a transcription for testing purposes.
        # In a real scenario, raw_audio_data would be sent to an ASR service.
        simulated_transcription = "What time is it in Tokyo?"  # Example for testing
        logger.info(
            f"Processing audio input from device {device_id} "
            f"at {self._get_current_utc_timestamp()}..."
        )

        logger.debug("Simulated ASR Transcription: '%s'", simulated_transcription)
        # --- End Dummy ASR Implementation ---

        return self.process_text_input(simulated_transcription, device_id)

    def _process_nlu(self, text: str) -> dict:  # This is already correct
        """Delegate NLU processing to the injected NLU service.

        Args:
        ----
            text: The text to be processed by the NLU service.

        Returns
        -------
            A dictionary containing the intent and entities from the NLU service.

        Raises
        ------
            NLUProcessingError: If the underlying NLU service encounters an error.

        """
        return self.nlu_service.process_nlu(text)

    def _get_or_create_user_id_for_device(self, device_id: uuid.UUID) -> uuid.UUID:
        """Create Placeholder for a method to associate a device_id with a user_id.

        For now, it simply returns the device_id as the user_id.
        In a real system, this would interact with a user management service.
        """
        if not isinstance(device_id, uuid.UUID):
            raise ValueError(f"Invalid device_id format: {device_id}. Expected a UUID.")
        # Logic to map device_id to user_id goes here.
        # For simplicity, we'll assume a 1:1 mapping for now or create a new user.
        logger.info("Associating device %s with a user_id...", device_id)
        return device_id

    def _get_current_utc_timestamp(self) -> datetime:
        """Return the current UTC timestamp."""
        # FIX: Removed local import, now uses pytz.utc
        return datetime.now(pytz.utc)  # <--- FIX: Use datetime.now(pytz.utc)
