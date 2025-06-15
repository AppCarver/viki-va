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
