"""error handling."""
# shared_libs/errors.py


class VikiError(Exception):
    """Base exception for all Viki-related errors."""

    pass


class NLUProcessingError(VikiError):
    """Exception raised for errors during Natural Language Understanding processing."""

    pass


class NLGGenerationError(VikiError):
    """Exception raised for errors during Natural Language Generation."""

    def __init__(
        self,
        message: str = "NLG generation failed.",
        original_exception: Exception | None = None,
    ):
        """Initialize the NLGGenerationError.

        This exception is raised when the Natural Language Generation process
        encounters an issue, such as an empty response from the LLM or a problem
        with the underlying API call.

        Args:
        ----
            message (str, optional): A descriptive error message.
            Defaults to "NLG generation failed.".
            original_exception (Exception, optional): The original exception that caused
                                                      this NLGGenerationError, if any.
                                                    Useful for debugging the root cause.

        """
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)


class ActionExecutionError(VikiError):
    """Exception raised for errors during action execution."""

    pass


class LongTermMemoryError(Exception):
    """Exception raised for errors during action execution."""

    pass


# Add other custom errors as needed
class ConversationLogError(Exception):
    """Exception raised for errors within the ConversationLog component."""

    def __init__(self, message: str) -> None:
        """Initialize the ConversationLogError with a message."""
        self.message = message
        super().__init__(self.message)


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
