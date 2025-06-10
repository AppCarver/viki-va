# Natural Language Understanding (NLU) Service

This directory contains the core components responsible for Natural Language Understanding (NLU) within the Viki Virtual Assistant.

## Purpose

The primary goal of the NLU service is to:
- **Abstract LLM/NLU Providers:** Provide a standardized interface (`NLUServiceInterface`) that allows the core system (like the `InputProcessor`) to interact with various Large Language Models (LLMs) or NLU providers without needing to know their specific implementation details.
- **Extract Intent and Entities:** Process raw text (or transcribed audio) user input to identify the user's `intent` (e.g., "get_time", "set_reminder") and extract relevant `entities` (e.g., "location", "item", "time").

## Key Components

-   `nlu_service_interface.py`: Defines the `NLUServiceInterface` Abstract Base Class (ABC). All NLU service implementations must adhere to this contract. This promotes dependency inversion and makes the system highly flexible.
-   `gemini_nlu_service.py`: A concrete implementation of `NLUServiceInterface` that utilizes Google's new Gen AI SDK (Gemini API) to perform NLU tasks. This is the default NLU provider for the Viki Assistant.

## How it Works

1.  The `InputProcessor` receives user input.
2.  It depends on an instance of `NLUServiceInterface` (e.g., `GeminiNLUService`) injected during its initialization.
3.  The `InputProcessor` calls the `process_nlu()` method on the injected service, passing the user's text.
4.  The specific NLU service implementation (e.g., `GeminiNLUService`) handles the communication with its underlying LLM/API, processes the response, and returns a standardized dictionary containing the `intent` and `entities`.

This architecture ensures that if you decide to switch from Gemini to another NLU provider (e.g., OpenAI, a local open-source LLM), you would primarily only need to create a new implementation of `NLUServiceInterface` and configure its injection, without modifying the `InputProcessor` itself.