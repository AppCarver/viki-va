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
from services.input_processor.src.input_processor import (
    InputProcessor,
    NLUProcessingError,
)
from services.nlu_service.src.gemini_nlu_service import GeminiNLUService

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
        # 1. Initialize the NLU Service (GeminiNLUService)
        print(f"Initializing Gemini NLU Service with model: {gemini_model_name}...")
        nlu_service = GeminiNLUService(model_name=gemini_model_name)
        print("Gemini NLU Service initialized successfully.")

        # 2. Initialize the Input Processor with the NLU Service
        print("Initializing Input Processor...")
        input_processor = InputProcessor(nlu_service=nlu_service)
        print("Input Processor initialized successfully.")

        # 3. Initialize the Action Executor
        print("Initializing Action Executor...")
        action_executor = ActionExecutor()  # <--- ADD THIS LINE
        print("Action Executor initialized successfully.")

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
            viki_response = action_executor.execute_action(
                nlu_result.get("intent", "unknown"), nlu_result.get("entities", {})
            )
            print(f"Viki: {viki_response}")

        except NLUProcessingError as e:
            print(f"Viki: I had trouble understanding that. NLU Error: {e}")
        except Exception as e:
            print(f"Viki: An unexpected error occurred: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main()
