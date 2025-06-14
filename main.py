"""Main entry point for the Viki Virtual Assistant application.

This module orchestrates the core components of the Viki VA,
specifically demonstrating the Natural Language Understanding (NLU)
pipeline. It initializes the Gemini NLU service and the Input Processor,
then enters a continuous loop to accept user input, process it for
intent and entities, and display the results.

Requires the 'GOOGLE_API_KEY' environment variable to be set for
Gemini API access. This is typically loaded from a .env file.
"""

import logging
import sys
import uuid

import dotenv

from services.action_executor.src.action_executor import (
    ActionExecutor,
)
from services.brain.language_center.nlg.src.gemini_nlg_service import GeminiNLGService
from services.brain.language_center.nlu.src.gemini_nlu_service import (
    GeminiNLUService,
)
from services.brain.language_center.src.language_center import LanguageCenter
from services.input_processor.src.input_processor import (
    InputProcessor,
    NLUProcessingError,
)

dotenv.load_dotenv()


def configure_application_logging() -> None:
    """Set up the global logging configuration for the entire Viki VA.

    This function should be called once at application startup.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # You can add multiple handlers here:
            logging.StreamHandler(sys.stdout),  # Logs to console
            # logging.FileHandler('application.log') # Example: logs to a file
        ],
    )
    # --- Add these lines to suppress third-party library verbosity ---
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    # -----------------------------------------------------------------


def main() -> None:
    """Run the Viki Virtual Assistant's main conversational loop.

    This function initializes the Natural Language Understanding (NLU) service
    (using Gemini) and the Input Processor. It then enters an interactive loop,
    prompting the user for input, processing it through the NLU pipeline, and
    displaying the extracted intent and entities.

    The application requires the 'GOOGLE_API_KEY' environment variable to be set
    for the Gemini NLU Service to initialize successfully.

    Allows the user to exit the conversation by typing 'exit' or 'quit'.

    Raises
    ------
        ValueError: If the 'GOOGLE_API_KEY' environment variable is not set
                    during the initialization of GeminiNLUService.
        Exception: Catches and reports any unexpected errors during the
                   initialization of core components or during user input
                   processing.

    """
    # Set up logging
    configure_application_logging()
    main_logger = logging.getLogger(__name__)
    main_logger.info("Viki VA Application is starting...")

    # --- Configuration and Initialization ---
    gemini_model_name = "gemini-1.5-flash"

    # Generate a dummy device ID for this session
    session_device_id = uuid.uuid4()

    try:
        # 1. Initialize NLU and NLG services
        nlu_service = GeminiNLUService(model_name=gemini_model_name)
        nlg_service = GeminiNLGService(model_name=gemini_model_name)

        # 2. Initialize the Language Center with both services
        main_logger.info("Initializing Language Center...")
        language_center = LanguageCenter(
            nlu_service=nlu_service,
            nlg_service=nlg_service,
            # short_term_memory_service=short_term_memory_instance
            #       # If you fetch context here
        )
        main_logger.info("Language Center initialized successfully.")

        # 3. Initialize the Input Processor with the Language Center
        #    (or just NLU service)
        # This depends on if InputProcessor specifically wants the NLU service
        # or LanguageCenter
        input_processor = InputProcessor(nlu_service=language_center.nlu_service)

        # 4. Initialize Action Executor
        action_executor = ActionExecutor()

    except ValueError as e:
        main_logger.error("Configuration Error: %s", e, exc_info=True)
        main_logger.debug(
            "Please ensure GOOGLE_API_KEY environment "
            "variable is set (e.g., in a .env file)."
        )
        return
    except Exception as e:
        main_logger.error(
            "An unexpected error occurred during initialization: %s",
            e,
            exc_info=True,
        )
        return

    main_logger.info(f"\nViki is ready! Using Device ID: {session_device_id}")
    main_logger.info("Type 'exit' or 'quit' to end the conversation.")

    # --- Main Interaction Loop ---
    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            main_logger.info("Viki: Goodbye!")
            break

        try:
            # Process user input using the InputProcessor
            main_logger.info("Processing input...")
            # Input Processor calls language_center.understand_user_input internally
            nlu_result = input_processor.process_text_input(
                user_input, session_device_id
            )

            # Print the NLU result (for debugging/observation)
            main_logger.debug("\n--- Viki's NLU Analysis ---")
            main_logger.info(f"  Intent: {nlu_result.get('intent', 'N/A')}")
            main_logger.info(f"  Entities: {nlu_result.get('entities', 'N/A')}")
            if nlu_result.get("error"):
                main_logger.debug(
                    f"  Error Message: {nlu_result.get('message', 'N/A')}"
                )

            # --- Call the Action Executor ---
            main_logger.debug("\n--- Viki's Action Execution ---")
            # Action Executor now provides a structured dictionary response
            action_executor_response = (
                action_executor.execute_action_and_get_structured_response(
                    nlu_result.get("intent", "unknown"), nlu_result.get("entities", {})
                )
            )

            # Process the structured response from Action Executor
            if action_executor_response.get("success"):
                # Extract dialogue_act and response_content from result_data
                # We assume dialogue_act is now passed within result_data
                # for clarity
                dialogue_act = action_executor_response["result_data"].get(
                    "dialogue_act"
                )
                response_content = action_executor_response["result_data"]

                # --- Direct Output for Simple Actions (for immediate testing) ---
                # This allows Viki to speak directly if ActionExecutor already has
                # a message.
                if "message" in response_content:
                    main_logger.info(
                        f"Viki (ActionExecutor direct): {response_content['message']}"
                    )
                    continue  # Skip NLG for direct message to see immediate output

                # Main calls Language Center for NLG
                main_logger.debug("\n--- Viki's Generated Response (via NLG) ---")
                viki_nlg_output = language_center.generate_response(
                    dialogue_act=dialogue_act,
                    response_content=response_content,
                    conversation_id=str(session_device_id),
                    user_id="user_viki_session",  # Dummy user ID for now
                )
                main_logger.debug(
                    f"Viki (NLG): {
                        viki_nlg_output.get(
                            'generated_text', 'I could not generate a response.'
                        )
                    }"
                )
            else:
                # Handle cases where Action Executor reports an error
                error_info = action_executor_response.get("error", {})
                error_code = error_info.get("code", "UNKNOWN_ERROR")
                error_message = error_info.get(
                    "message", "An unexpected action error occurred."
                )
                main_logger.error(
                    f"ActionExecutor Error [{error_code}]: {error_message}"
                )
                main_logger.info(f"Viki: {error_message}")

        except NLUProcessingError as e:
            main_logger.error(
                "Viki: I had trouble understanding that. NLU Error: %s",
                e,
                exc_info=True,
            )
        except Exception as e:
            main_logger.error(
                "Viki: An unexpected error occurred: %s", e, exc_info=True
            )
            main_logger.info("Please try again.")


if __name__ == "__main__":
    main()
