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
from unittest.mock import MagicMock
from uuid import UUID  # Explicitly import UUID for type consistency

import dotenv

from services.action_executor.src.action_executor import (
    ActionExecutor,
)
from services.brain.language_center.nlg.src.gemini_nlg_service import GeminiNLGService
from services.brain.language_center.nlu.src.gemini_nlu_service import (
    GeminiNLUService,
)
from services.brain.language_center.src.language_center import LanguageCenter
from services.brain.pre_forntal_cortex.src.pre_frontal_cortex import PrefrontalCortex

## NEW CODE (FROM PREVIOUS STEPS) ##
from services.brain.short_term_mem.src.short_term_memory import ShortTermMemory
from services.input_processor.src.input_processor import (
    InputProcessor,
    NLUProcessingError,
)

## END NEW CODE (FROM PREVIOUS STEPS) ##
# --- NEW IMPORTS FOR OutputManager ---
from services.output_manager.src.output_manager import OutputManager

# --- END NEW IMPORTS ---

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
    # For a single session, we'll use a consistent user_id
    session_user_id = uuid.uuid4()

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
        input_processor = InputProcessor(nlu_service=language_center.nlu_service)

        # 4. Initialize Action Executor
        action_executor = ActionExecutor()

        ## NEW CODE (from previous steps): Initialize
        ## ShortTermMemory and PrefrontalCortex ##
        short_term_memory = ShortTermMemory()
        long_term_memory = MagicMock()

        prefrontal_cortex = PrefrontalCortex(
            short_term_memory=short_term_memory,
            action_executor=action_executor,
            long_term_memory=long_term_memory,
        )
        main_logger.info(
            "ShortTermMemory, ActionExecutor, and PrefrontalCortex initialized."
        )
        ## END NEW CODE (from previous steps) ##

        # --- NEW CODE: Initialize OutputManager ---
        output_manager = OutputManager()
        main_logger.info("OutputManager initialized.")
        # --- END NEW CODE ---

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
    # We'll use the session_device_id as the
    # conversation_id for simplicity in this demo.
    conversation_id_for_session = session_device_id
    # Define a consistent device ID for console interactions
    console_device_id = "console_default_device"

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            main_logger.info("Viki: Goodbye!")
            # Optionally, use OutputManager for goodbye message
            # output_manager.send_response(
            #     conversation_id=UUID(conversation_id_for_session),
            #     user_id=UUID(session_user_id),
            #     device_id=console_device_id,
            #     va_response_text="Goodbye! Have a great day!"
            # )
            break

        try:
            main_logger.info("Processing input...")
            # Get the NLU result from the InputProcessor.
            # InputProcessor.process_text_input returns the NLU result directly.
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

            ## MODIFIED CODE: Pass NLU result to PrefrontalCortex ##
            main_logger.debug("\n--- Viki's Dialogue Management (PrefrontalCortex) ---")

            # Generate a turn_id for the current interaction
            current_turn_id = uuid.uuid4()

            pfc_response = prefrontal_cortex.process_dialogue_turn(
                turn_id=current_turn_id,
                conversation_id=conversation_id_for_session,
                user_id=session_user_id,
                processed_text=user_input,  # Use the raw user input here
                nlu_results=nlu_result,  # Pass the NLU results directly
            )

            # Check if PrefrontalCortex successfully processed the turn
            if pfc_response["success"]:
                va_response_text = pfc_response["va_response_text"]
                action_taken = pfc_response["action_taken"]
                new_dialogue_state = pfc_response["new_dialogue_state"]

                main_logger.debug(f"  Action Taken: {action_taken}")
                main_logger.debug(f"  New Dialogue State: {new_dialogue_state}")

                # --- NEW CODE: Use OutputManager to deliver Viki's response ---
                delivery_result = output_manager.send_response(
                    conversation_id=UUID(str(conversation_id_for_session)),
                    user_id=UUID(str(session_user_id)),
                    device_id=console_device_id,
                    va_response_text=va_response_text,
                    # output_format_hints=pfc_response.get("output_format_hints")
                    # ^ Uncomment this if PFC will return format hints
                )

                if not delivery_result["success"]:
                    main_logger.error(
                        f"Failed to deliver response: {delivery_result['error']}"
                    )
                # --- END NEW CODE ---

            else:
                # Handle cases where PrefrontalCortex reports an error
                error_message = pfc_response.get(
                    "error", "An unexpected error occurred in PrefrontalCortex."
                )
                main_logger.error(f"PrefrontalCortex Error: {error_message}")
                # --- NEW CODE: Use OutputManager to deliver PFC error message ---
                delivery_result = output_manager.send_response(
                    conversation_id=UUID(str(conversation_id_for_session)),
                    user_id=UUID(str(session_user_id)),
                    device_id=console_device_id,
                    va_response_text=f"I apologize, but an internal error "
                    f"occurred: {error_message} Please try again.",
                )
                if not delivery_result["success"]:
                    main_logger.error(
                        f"Failed to deliver PFC error message: "
                        f"{delivery_result['error']}"
                    )
                # --- END NEW CODE ---

            ## END MODIFIED CODE ##

        except NLUProcessingError as e:
            main_logger.error(
                "Viki: I had trouble understanding that. NLU Error: %s",
                e,
                exc_info=True,
            )
            # --- NEW CODE: Use OutputManager to deliver NLU error message ---
            delivery_result = output_manager.send_response(
                conversation_id=UUID(str(conversation_id_for_session)),
                user_id=UUID(str(session_user_id)),
                device_id=console_device_id,
                va_response_text="I'm sorry, I couldn't understand your input.",
            )
            if not delivery_result["success"]:
                main_logger.error(
                    f"Failed to deliver NLU error message: {delivery_result['error']}"
                )
            # --- END NEW CODE ---
        except Exception as e:
            main_logger.error(
                "Viki: An unexpected error occurred: %s", e, exc_info=True
            )
            # --- NEW CODE: Use OutputManager to deliver general error message ---
            delivery_result = output_manager.send_response(
                conversation_id=UUID(str(conversation_id_for_session)),
                user_id=UUID(str(session_user_id)),
                device_id=console_device_id,
                va_response_text="Something went wrong. Please try again.",
            )
            if not delivery_result["success"]:
                main_logger.error(
                    f"Failed to deliver general error message: "
                    f"{delivery_result['error']}"
                )
            # --- END NEW CODE ---


if __name__ == "__main__":
    main()
