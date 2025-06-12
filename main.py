# main.py

"""Main entry point for the Viki Virtual Assistant application.

This module orchestrates the core components of the Viki VA,
specifically demonstrating the Natural Language Understanding (NLU)
pipeline. It initializes the Gemini NLU service and the Input Processor,
then enters a continuous loop to accept user input, process it for
intent and entities, and display the results.

Requires the 'GOOGLE_API_KEY' environment variable to be set for
Gemini API access. This is typically loaded from a .env file.
"""

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
                   initialization of core components or during user input processing.

    """
    # --- Configuration and Initialization ---
    gemini_model_name = "gemini-1.5-flash"

    # Generate a dummy device ID for this session
    session_device_id = uuid.uuid4()

    try:
        # 1. Initialize NLU and NLG services
        nlu_service = GeminiNLUService(model_name=gemini_model_name)
        nlg_service = GeminiNLGService(model_name=gemini_model_name)

        # 2. Initialize the Language Center with both services
        print("Initializing Language Center...")
        language_center = LanguageCenter(
            nlu_service=nlu_service,
            nlg_service=nlg_service,
            # short_term_memory_service=short_term_memory_instance
            #       # If you fetch context here
        )
        print("Language Center initialized successfully.")

        # 3. Initialize the Input Processor with the Language Center
        #    (or just NLU service)
        # This depends on if InputProcessor specifically wants the NLU service
        # or LanguageCenter
        input_processor = InputProcessor(nlu_service=language_center.nlu_service)

        # 4. Initialize Action Executor
        action_executor = ActionExecutor()

    except ValueError as e:
        print(f"Configuration Error: {e}")
        print(
            "Please ensure GOOGLE_API_KEY environment "
            "variable is set (e.g., in a .env file)."
        )
        return
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}")
        return

    print(f"\nViki is ready! Using Device ID: {session_device_id}")
    print("Type 'exit' or 'quit' to end the conversation.")

    # --- Main Interaction Loop ---
    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Viki: Goodbye!")
            break

        try:
            # Process user input using the InputProcessor
            print("Processing input...")
            # Input Processor calls language_center.understand_user_input internally
            nlu_result = input_processor.process_text_input(
                user_input, session_device_id
            )

            # Print the NLU result (for debugging/observation)
            print("\n--- Viki's NLU Analysis ---")
            print(f"  Intent: {nlu_result.get('intent', 'N/A')}")
            print(f"  Entities: {nlu_result.get('entities', 'N/A')}")
            # You can uncomment these if you want to see all details again
            # print(f"  Processed Text: {nlu_result.get('processed_text', 'N/A')}")
            # print(f"  User ID: {nlu_result.get('user_id', 'N/A')}")
            # print(f"  Device ID: {nlu_result.get('device_id', 'N/A')}")
            # print(f"  Timestamp: {nlu_result.get('timestamp', 'N/A')}")
            if nlu_result.get("error"):
                print(f"  Error Message: {nlu_result.get('message', 'N/A')}")

            # --- Call the Action Executor ---
            print("\n--- Viki's Response ---")
            # Action Executor provides structured data
            dialogue_act, response_content = (
                action_executor.execute_action_and_get_structured_response(
                    nlu_result.get("intent", "unknown"), nlu_result.get("entities", {})
                )
            )

            # Main calls Language Center for NLG
            print("\n--- Viki's Generated Response ---")
            viki_nlg_output = language_center.generate_response(
                dialogue_act=dialogue_act,
                response_content=response_content,
                conversation_id=str(
                    session_device_id
                ),  # FIX APPLIED HERE: Converted UUID to string
                user_id="user_viki_session",  # Dummy user ID for now
            )
            print(
                f"Viki: {
                    viki_nlg_output.get(
                        'generated_text', 'I could not generate a response.'
                    )
                }"
            )

        except NLUProcessingError as e:
            print(f"Viki: I had trouble understanding that. NLU Error: {e}")
        except Exception as e:
            print(f"Viki: An unexpected error occurred: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main()
