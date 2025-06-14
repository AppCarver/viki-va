"""Unit tests for the OutputManager component.

Responsible for delivering Viki's responses to users.
"""

import logging
from unittest.mock import MagicMock, patch  # Import MagicMock
from uuid import UUID, uuid4

import pytest

# Import the OutputManager and its custom exceptions
from services.output_manager.src.output_manager import (
    OutputManager,
)


# Define a fixture for OutputManager instance setup
@pytest.fixture
def output_manager_instance():
    """Provide a fresh OutputManager instance for each test."""
    manager = OutputManager()
    manager.logger.setLevel(logging.INFO)
    return manager


# Define a fixture for patching builtins.print
@pytest.fixture
def mock_print(monkeypatch):
    """Mock builtins.print for testing console output."""
    mocked_print = patch("builtins.print").start()
    yield mocked_print
    patch.stopall()  # Ensure all patches are stopped after the test


class TestOutputManager:
    """Test output mangaer."""

    # Class-level test data
    test_conversation_id: UUID = uuid4()
    test_user_id: UUID = uuid4()
    test_device_id: str = "console_default_device"
    test_response_text: str = "This is a test response."

    def test_send_response_success(
        self, output_manager_instance: OutputManager, mock_print, caplog
    ):
        """Test that send_response successfully delivers a response to the console."""
        with caplog.at_level(logging.INFO):
            result = output_manager_instance.send_response(
                conversation_id=self.test_conversation_id,
                user_id=self.test_user_id,
                device_id=self.test_device_id,
                va_response_text=self.test_response_text,
            )

        assert result["success"] is True
        assert result["delivery_status"] == "SENT"
        assert result["error"] is None
        mock_print.assert_called_once_with(f"Viki: {self.test_response_text}")

        assert "Attempting to send response" in caplog.text
        assert "Viki (to console device console_default_device):" in caplog.text
        assert self.test_response_text in caplog.text

    def test_send_response_device_not_found(
        self, output_manager_instance: OutputManager, caplog
    ):
        """Test that send_response handles an unknown device_id."""
        with caplog.at_level(logging.ERROR):
            unknown_device_id = "non_existent_device"
            result = output_manager_instance.send_response(
                conversation_id=self.test_conversation_id,
                user_id=self.test_user_id,
                device_id=unknown_device_id,
                va_response_text=self.test_response_text,
            )

        assert result["success"] is False
        assert result["delivery_status"] == "FAILED"
        assert result["error"] is not None
        assert result["error"]["code"] == "DEVICE_NOT_FOUND"
        assert (
            f"Device ID '{unknown_device_id}' not found" in result["error"]["message"]
        )

        assert "Delivery failed: Device ID" in caplog.text

    def test_send_response_unsupported_output_capability(
        self, output_manager_instance: OutputManager, caplog
    ):
        """Test that send_response handles a device not supporting text output."""
        unsupported_device_id = "device_no_text"
        output_manager_instance._device_registry[unsupported_device_id] = {
            "type": "special_device",
            "capabilities": ["no_text_here"],
        }

        with caplog.at_level(logging.ERROR):
            result = output_manager_instance.send_response(
                conversation_id=self.test_conversation_id,
                user_id=self.test_user_id,
                device_id=unsupported_device_id,
                va_response_text=self.test_response_text,
            )

        assert result["success"] is False
        assert result["delivery_status"] == "FAILED"
        assert result["error"] is not None
        assert result["error"]["code"] == "UNSUPPORTED_OUTPUT"
        assert f"Device '{unsupported_device_id}'" in result["error"]["message"]
        assert "does not support text output" in result["error"]["message"]

        assert "Delivery failed: Device" in caplog.text

    def test_send_response_general_exception(
        self, output_manager_instance: OutputManager, caplog
    ):
        """Test that send_response handles a general unexpected exception."""
        # Create a mock for the entire _device_registry dictionary
        mock_device_registry = MagicMock()
        # Configure the 'get' method of this mock to raise an exception
        mock_device_registry.get.side_effect = Exception(
            "Simulated unexpected registry error!"
        )

        # Temporarily replace the actual _device_registry with our mock
        with patch.object(
            output_manager_instance, "_device_registry", new=mock_device_registry
        ):
            with caplog.at_level(logging.ERROR):
                result = output_manager_instance.send_response(
                    conversation_id=self.test_conversation_id,
                    user_id=self.test_user_id,
                    device_id=self.test_device_id,
                    va_response_text=self.test_response_text,
                )

            assert result["success"] is False
            assert result["delivery_status"] == "FAILED"
            assert result["error"] is not None
            assert result["error"]["code"] == "UNKNOWN_ERROR"
            assert "Simulated unexpected registry error!" in result["error"]["message"]

            assert (
                "An unexpected error occurred during response delivery to"
                in caplog.text
            )
            assert "Simulated unexpected registry error!" in caplog.text
            assert "Traceback (most recent call last):" in caplog.text

    def test_send_response_with_output_format_hints(
        self, output_manager_instance: OutputManager
    ):
        """Test that send_response accepts output_format_hints without failing.

        (though current implementation doesn't use them).
        """
        hints = {"tts_voice": "female_1", "rich_ui_elements": []}
        result = output_manager_instance.send_response(
            conversation_id=self.test_conversation_id,
            user_id=self.test_user_id,
            device_id=self.test_device_id,
            va_response_text=self.test_response_text,
            output_format_hints=hints,
        )
        assert result["success"] is True
        assert result["error"] is None
