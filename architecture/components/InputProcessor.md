# Component Specification: InputProcessor

---

**1. Component Name:** `InputProcessor`

**2. Conceptual Role / Nickname:** "Ears" / "Text Osmosis Point"

**3. Purpose / Mission:**
The `InputProcessor` is the primary entry point for all user-initiated communication. Its mission is to reliably receive raw user input (audio or text), transform it into a standardized textual format, **orchestrate the interpretation of this text into a user intent and relevant entities via an external Natural Language Understanding (NLU) model,** and accurately pass through user and device identification for subsequent processing.

---

**4. Core Responsibilities:**

* **Input Reception:** Accept raw audio streams or direct text strings from various `Device` types.
* **Speech-to-Text (ASR) Orchestration:** For audio input, utilize and manage calls to an ASR service/model (e.g., Gemini-FLASH ASR) to transcribe spoken words into a text string.
* **Text Normalization:** Standardize the processed text (e.g., trim whitespace, handle basic punctuation, initial casing, remove non-printable characters) *after* ASR and *before* NLU.
* **Natural Language Understanding (NLU) Orchestration:** Utilize and manage calls to an NLU service/model (e.g., Gemini-FLASH) to interpret the user's standardized text input and extract the user's `intent` and any associated `entities`.
* **Input Context Passing:** Accurately pass through identification for the originating `User` and `Device` to ensure subsequent components have the necessary context.
* **Structured Handover:** Prepare and provide the **structured NLU result (intent, entities, and the processed text itself)** along with the user/device context to the `ActionExecutor`.

---

**5. External Interfaces / APIs:**

This component exposes the following public functions for other parts of the system to interact with it:

* `process_audio_input(raw_audio_data, device_id, metadata=None)`
* `process_text_input(raw_text_string, device_id, metadata=None)`

#### API Definition: `process_audio_input`

* **Description:** Processes raw audio input from a user. Orchestrates ASR and NLU to extract intent and entities.
* **Parameters:**
    * `raw_audio_data` (`bytes`): The raw audio binary data (e.g., WAV, MP3 stream).
    * `device_id` (`UUID`): The unique identifier of the `Device` from which the audio originated.
    * `metadata` (`dict`, optional): Additional context about the input, e.g., `{'audio_format': 'wav', 'locale': 'en-US'}`. Default is `None`.
* **Returns:** (`dict`) A dictionary containing the processing outcome, including the NLU result:

    ```json
    {
        "success": true,            // True if intent was successfully recognized (not 'unknown')
        "message": "string",        // A descriptive message about processing
        "device_id": "UUID",        // The original device_id passed in
        "user_id": "UUID",          // The identified user_id (if User & Device Identification is implemented)
        "processed_text": "string", // The transcribed and normalized text
        "intent": "string",         // The detected intent (e.g., "greet", "get_time", "unknown")
        "entities": {},             // Dictionary of extracted entities (e.g., {"location": "London"})
        "error": "string"           // Optional: error message if processing failed
    }
    ```
* **Possible Errors:**
    * `InvalidDeviceError`: `device_id` not found or invalid.
    * `ASRTranscriptionError`: Failure in converting audio to text.
    * `NLUProcessingError`: Failure in extracting intent/entities from the text (e.g., API call failed, invalid response).

#### API Definition: `process_text_input`

* **Description:** Processes direct text input from a user. Orchestrates NLU to extract intent and entities.
* **Parameters:**
    * `raw_text_string` (`str`): The raw text string provided by the user.
    * `device_id` (`UUID`): The unique identifier of the `Device` from which the text originated.
    * `metadata` (`dict`, optional): Additional context, e.g., `{'source_channel': 'web_chat', 'locale': 'en-US'}`. Default is `None`.
* **Returns:** (`dict`) Same structure as `process_audio_input`'s return.
* **Possible Errors:**
    * `InvalidDeviceError`: `device_id` not found or invalid.
    * `NLUProcessingError`: Failure in extracting intent/entities from the text (e.g., API call failed, invalid response).

---

**6. Internal Logic / Algorithm (Detailed Steps):**

This algorithm applies to both `process_audio_input` (after ASR) and `process_text_input` after initial processing.

* **Step 1: Input Pre-processing & Timestamping:**
    * `current_timestamp` = Get current system time.
    * IF `process_audio_input` invoked:
        * Call ASR service (e.g., Gemini-FLASH ASR API) to convert `raw_audio_data` to `transcribed_text`.
        * Handle ASR failures (e.g., empty transcription, errors).
    * ELSE (`process_text_input` invoked):
        * `transcribed_text` = `raw_text_string`.
    * `processed_text` = `transcribed_text`.strip() (Apply basic text normalization, e.g., trim whitespace, handle basic punctuation).

* **Step 2: User and Device Identification:**
    * Query `Device` data model using `device_id`.
    * IF `Device` record not found:
        * Log error (`InvalidDeviceError`).
        * Return `success: False` with an `error` message.
    * `user_id` = `Device.owner_user_id`.
    * IF `user_id` is null or invalid:
        * Log error (`UserIdentificationError`).
        * Return `success: False` with an `error` message (or trigger separate user identification flow if designed).

* **Step 3: Natural Language Understanding (NLU) Orchestration:**
    * Prepare a prompt for the NLU service/model (e.g., Gemini-FLASH) using `processed_text` to request intent and entity extraction in a structured format (e.g., JSON).
    * Call the NLU service/model API with the prompt and `processed_text`.
    * Parse the response from the NLU service/model.
    * IF NLU service/model fails or returns unparseable/invalid response:
        * Log error (`NLUProcessingError`).
        * Set `intent` = "unknown".
        * Set `entities` = `{"raw_query": processed_text}`.
        * Set `success` = `False`.
    * ELSE:
        * Extract `intent` and `entities` from the NLU service/model's parsed response.
        * Set `success` = `True` (if a valid intent was recognized, otherwise `False`).

* **Step 4: Handover / Return Results:**
    * Return the processed information to the caller (e.g., `ActionExecutor` or a higher-level orchestrator):
        * `success` (from Step 3)
        * `message` (descriptive message based on processing)
        * `device_id` (input parameter)
        * `user_id` (from Step 2)
        * `processed_text` (from Step 1)
        * `intent` (from Step 3)
        * `entities` (from Step 3)
        * `error` (if any occurred)

---

**7. Data Interactions:**

* **Reads from:**
    * **`Device`**: To retrieve the `owner_user_id` for the given `device_id`.
* **Writes to:**
    * **None directly for logging conversation turns.** (This is handled by a higher-level component like `ConversationManager` using the `InputProcessor`'s output).

---

**8. Dependencies:**

* **ASR Service/Library:** (e.g., Google Cloud Speech-to-Text API, Gemini-FLASH ASR capabilities, local ASR model) – for `process_audio_input`.
* **NLU Service/Library:** (e.g., Google Gemini-FLASH API, local NLU/LLM model like a Hugging Face model) – for both `process_audio_input` and `process_text_input`.
* **UUID Generation Library:** For generating unique identifiers (though `device_id` is passed in).
* **Database Access Layer / ORM:** Specifically for interacting with the `Device` data model (to get `user_id`).
* **Logging Framework:** For system logging and error reporting.

---

**9. Assumptions / Constraints:**

* All incoming inputs will always provide a valid `device_id`.
* Each `Device` is consistently linked to a single `User` via `owner_user_id`.
* ASR and NLU are handled by separate, integrated services/models; `InputProcessor` is responsible for calling them, not implementing the core ML models themselves.
* NLU service/model is expected to return intent and entities in a predictable, structured format (e.g., JSON).

---

**10. Collaboration Strategy on GitHub:**

* **Repository Structure:** Maintain a clear `docs/components/` directory.
* **Naming Convention:** Use consistent file names like `ComponentName.md` (e.g., `InputProcessor.md`).
* **Markdown's Simplicity:** It's plain text, so it's easy to read, edit, and understand diffs (changes) in Git. Anyone with a text editor can contribute.
* **GitHub Rendering:** GitHub automatically renders Markdown files beautifully in the browser, making them easy to view without needing to clone the repo or use special tools.
* **Pull Request Workflow:** All changes to these `md` files go through the standard Git Pull Request (PR) review process, allowing for discussion, feedback, and version history.
* **Embedded Diagrams:** If you have diagrams, save them as `.drawio` (the source file for diagrams.net/draw.io) or export them as `.svg` (scalable vector graphics) or `.png` images, store them in a subfolder like `docs/components/images/`, and embed them directly in your Markdown using relative paths: `![Diagram Description](images/my_component_diagram.png)`.