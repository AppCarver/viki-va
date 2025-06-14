"""Contain the concrete implementation of the OutputManager.

Responsible for delivering Viki's responses to users.

It adheres to the OutputManagerInterface and handles content adaptation
and delivery to various channels (initially console, with future support
for TTS, rich media, and different messaging platforms).
"""

import logging
from typing import Any
from uuid import UUID

from .output_manager_interface import OutputManagerInterface


# Define custom errors as per spec (ideally in shared_libs/errors/errors.py)
# If you haven't already, consider moving these to shared_libs/errors/errors.py
# and importing them from there. For now, they're kept local for completeness.
class DeviceNotFoundError(Exception):
    """Raised when a device_id is not found in the registry."""

    pass


class UnsupportedOutputError(Exception):
    """Raise when a device's capabilities don't match requested output."""

    pass


class TTSConversionError(Exception):
    """Raised when Text-to-Speech conversion fails."""

    pass


class DeliveryChannelError(Exception):
    """Raised when there's an issue sending via the specific platform API."""

    pass


class OutputManager(OutputManagerInterface):
    """Manages the output of Viki's responses to various channels.

    This class handles how Viki's generated responses are presented to the
    user, adapting to various modalities (text, voice, rich media) and device
    capabilities.
    """

    def __init__(self) -> None:
        """Initialize the OutputManager.

        Sets up the logger and a basic in-memory device registry.
        The device registry is a placeholder for a more robust system
        that would store device capabilities and configurations.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self._device_registry = {
            "console_default_device": {
                "type": "console",
                "capabilities": ["text_output"],
            }
        }
        self.logger.info("OutputManager initialized.")

    def send_response(
        self,
        conversation_id: UUID,
        user_id: UUID,
        device_id: str,
        va_response_text: str,
        output_format_hints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Deliver a natural language response to a specified user device.

        Adapting it to the device's capabilities.

        Args:
            conversation_id (UUID): The ID of the conversation.
            user_id (UUID): The ID of the user to whom the response is
                addressed.
            device_id (str): A unique identifier for the specific device or
                communication channel.
            va_response_text (str): The final natural language text generated
                by Viki.
            output_format_hints (dict, optional): Additional hints for desired
                output formatting.

        Returns:
            Dict[str, Any]: A dictionary indicating the outcome of the delivery
                attempt. Expected keys: "success", "delivery_status",
                "message_id", "error".

        """
        self.logger.info(
            f"Attempting to send response to device '{device_id}' for user "
            f"'{user_id}' in conversation '{conversation_id}'"
        )

        try:
            device_config = self._device_registry.get(device_id)
            if not device_config:
                raise DeviceNotFoundError(
                    f"Device ID '{device_id}' not found in registry."
                )

            device_type = device_config.get("type")
            device_capabilities = device_config.get("capabilities", [])

            if "text_output" not in device_capabilities:
                raise UnsupportedOutputError(
                    f"Device '{device_id}' ({device_type}) does not "
                    "support text output."
                )

            formatted_response = va_response_text

            self.logger.info(
                f"Viki (to {device_type} device {device_id}): {formatted_response}"
            )
            print(f"Viki: {formatted_response}")

            return {
                "success": True,
                "delivery_status": "SENT",
                "message_id": None,
                "error": None,
            }

        except DeviceNotFoundError as e:
            self.logger.error(f"Delivery failed: {e}", exc_info=True)
            return {
                "success": False,
                "delivery_status": "FAILED",
                "error": {"code": "DEVICE_NOT_FOUND", "message": str(e)},
            }
        except UnsupportedOutputError as e:
            self.logger.error(f"Delivery failed: {e}", exc_info=True)
            return {
                "success": False,
                "delivery_status": "FAILED",
                "error": {"code": "UNSUPPORTED_OUTPUT", "message": str(e)},
            }
        except Exception as e:
            self.logger.exception(
                f"An unexpected error occurred during response delivery to "
                f"'{device_id}'."
            )
            return {
                "success": False,
                "delivery_status": "FAILED",
                "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
            }


# --- For basic local testing ---
if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    from uuid import uuid4

    # Example usage:
    manager = OutputManager()
    try:
        conversation_id = uuid4()
        user_id = uuid4()
        device_id = "console_default_device"
        response_text = "Hello! I am Viki, your virtual assistant."

        print("\n--- Testing send_response ---")
        result = manager.send_response(
            conversation_id=conversation_id,
            user_id=user_id,
            device_id=device_id,
            va_response_text=response_text,
        )
        print("Result: {result}")

        # Example for a non-existent device
        print("\n--- Testing non-existent device ---")
        result_fail_device = manager.send_response(
            conversation_id=conversation_id,
            user_id=user_id,
            device_id="unknown_device",
            va_response_text="This should fail.",
        )
        print(f"Result (unknown device): {result_fail_device}")

        # Example for unsupported capability
        # (if you add such a device to _device_registry for testing)
        manager._device_registry["unsupported_text_device"] = {
            "type": "audio_only",
            "capabilities": ["audio_output"],
        }
        print("\n--- Testing unsupported capability ---")
        result_fail_capability = manager.send_response(
            conversation_id=conversation_id,
            user_id=user_id,
            device_id="unsupported_text_device",
            va_response_text="This should also fail.",
        )
        print(f"Result (unsupported capability): {result_fail_capability}")

    except Exception as e:
        manager.logger.error(f"An error occurred during standalone test: {e}")
