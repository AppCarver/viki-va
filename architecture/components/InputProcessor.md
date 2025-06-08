# Component Specification: InputProcessor

**1. Component Name:** `InputProcessor`

**2. Conceptual Role / Nickname:** "Ears" / "Text Osmosis Point"

**3. Purpose / Mission:**
The `InputProcessor` is the primary entry point for all user-initiated communication. Its mission is to reliably receive raw user input (audio or text), transform it into a standardized textual format, identify the originating user and device, and accurately log this interaction as a `ConversationTurn` within the appropriate `Conversation` context, ensuring seamless cross-device continuity.

**4. Core Responsibilities:**

* **Input Reception:** Accept raw audio streams or direct text strings from various `Device` types.
* **Speech-to-Text (ASR):** For audio input, utilize an ASR service to transcribe spoken words into a text string.
* **Text Normalization:** Standardize the processed text (e.g., trim whitespace, handle basic punctuation, initial casing, remove non-printable characters).
* **User & Device Identification:** Ascertain the `User` and `Device` associated with the input.
* **Conversation Continuity Determination:** Evaluate if the new input belongs to an existing active `Conversation` for the `User`, or if a new `Conversation` needs to be initiated, **regardless of the specific device used for the input**.
* **Conversation & Turn Logging:** Create and update records in the `Conversation` and `ConversationTurn` data models, maintaining a complete history of user interactions.
* **Handover:** Prepare and provide the processed input data to the next component in the processing pipeline (e.g., `brain:language_center` for NLU).

---

**5. External Interfaces / APIs:**

This component exposes the following public functions for other parts of the system to interact with it:

* `process_audio_input(raw_audio_data, device_id, metadata=None)`
* `process_text_input(raw_text_string, device_id, metadata=None)`

#### API Definition: `process_audio_input`

* **Description:** Processes raw audio input from a user. Performs ASR, determines conversation context, and logs the turn.
* **Parameters:**
    * `raw_audio_data` (`bytes`): The raw audio binary data (e.g., WAV, MP3 stream).
    * `device_id` (`UUID`): The unique identifier of the `Device` from which the audio originated.
    * `metadata` (`dict`, optional): Additional context about the input, e.g., `{'audio_format': 'wav', 'locale': 'en-US'}`. Default is `None`.
* **Returns:** (`dict`) A dictionary containing the processing outcome:

    ```json
    {
        "success": true,            
        "turn_id": "UUID",            
        "conversation_id": "UUID",    
        "user_id": "UUID",            
        "processed_text": "string",      
        "error": "string"           
    }
    ```
* **Possible Errors:**
    * `InvalidDeviceError`: `device_id` not found or invalid.
    * `UserIdentificationError`: Cannot determine the `User` associated with the device.
    * `ASRTranscriptionError`: Failure in converting audio to text.
    * `DatabaseError`: Issues writing to `Conversation` or `ConversationTurn` models.

#### API Definition: `process_text_input`

* **Description:** Processes direct text input from a user. Determines conversation context and logs the turn.
* **Parameters:**
    * `raw_text_string` (`str`): The raw text string provided by the user.
    * `device_id` (`UUID`): The unique identifier of the `Device` from which the text originated.
    * `metadata` (`dict`, optional): Additional context, e.g., `{'source_channel': 'web_chat', 'locale': 'en-US'}`. Default is `None`.
* **Returns:** (`dict`) Same structure as `process_audio_input`'s return.
* **Possible Errors:**
    * `InvalidDeviceError`: `device_id` not found or invalid.
    * `UserIdentificationError`: Cannot determine the `User` associated with the device.
    * `DatabaseError`: Issues writing to `Conversation` or `ConversationTurn` models.

---

**6. Internal Logic / Algorithm (Detailed Steps):**

This algorithm applies to both `process_audio_input` (after ASR) and `process_text_input`.

* **Step 1: Input Pre-processing & Timestamping:**
    * `current_timestamp` = Get current system time.
    * IF `process_audio_input` invoked:
        * Call ASR service to convert `raw_audio_data` to `transcribed_text`.
        * Handle ASR failures (e.g., empty transcription, errors).
    * ELSE (`process_text_input` invoked):
        * `transcribed_text` = `raw_text_string`.
    * `processed_text` = `transcribed_text`.strip() (Apply basic text normalization).

* **Step 2: User and Device Identification:**
    * Query `Device` data model using `device_id`.
    * IF `Device` record not found:
        * Log error (`InvalidDeviceError`).
        * Return `success: False`.
    * `user_id` = `Device.owner_user_id`.
    * IF `user_id` is null or invalid:
        * Log error (`UserIdentificationError`).
        * Return `success: False` (or trigger separate user identification flow if designed).

* **Step 3: Conversation Continuity Determination:**
    * Define `INACTIVITY_THRESHOLD` (e.g., 5 minutes, centrally configured).
    * Query `Conversation` data model:
        * Filter by `user_id` (from Step 2).
        * Order by `last_activity_timestamp` DESC.
        * Optionally filter by `status = 'active'` (if `pre-frontal_cortex` explicitly marks completed conversations as `inactive`).
        * `latest_conversation` = Retrieve the single most recent matching `Conversation` record.
    * IF `latest_conversation` EXISTS AND `(current_timestamp - latest_conversation.last_activity_timestamp)` is LESS THAN `INACTIVITY_THRESHOLD`:
        * `conversation_id` = `latest_conversation.conversation_id`
        * `is_new_conversation` = FALSE
    * ELSE:
        * `conversation_id` = Generate new UUID for `conversation_id`.
        * `is_new_conversation` = TRUE

* **Step 4: Conversation Data Model Update:**
    * IF `is_new_conversation` IS TRUE:
        * Create a new record in `Conversation` data model (`brain:long_term_mem`):
            * `conversation_id` (from Step 3)
            * `user_id` (from Step 2)
            * `start_timestamp` = `current_timestamp`
            * `last_activity_timestamp` = `current_timestamp`
            * `status` = 'active'
    * ELSE (`is_new_conversation` IS FALSE):
        * Update the existing `Conversation` record (identified by `conversation_id` from Step 3):
            * Set `last_activity_timestamp` = `current_timestamp`.
            * Set `status` = 'active' (in case it was implicitly timed-out but now resumed).

* **Step 5: Conversation Turn Logging:**
    * `turn_id` = Generate new UUID for `turn_id`.
    * Create a new record in `ConversationTurn` data model (`brain:conversationLog`):
        * `turn_id` (from this step)
        * `conversation_id` (from Step 3/4)
        * `user_id` (from Step 2)
        * `device_id` (input parameter)
        * `speaker` = 'User'
        * `text` = `processed_text` (from Step 1)
        * `timestamp` = `current_timestamp` (from Step 1)

* **Step 6: Handover / Return Results:**
    * Return the processed information to the caller (e.g., `brain:pre-frontal_cortex`):
        * `success: True`, `turn_id`, `conversation_id`, `user_id`, `processed_text`.

---

**7. Data Interactions:**

* **Reads from:**
    * **`Device`**: To retrieve the `owner_user_id` for the given `device_id`.
    * **`Conversation`**: To identify an existing, active conversation for the `user_id`.
* **Writes to:**
    * **`Conversation`**: When a new conversation is initiated, or an existing one is updated with a new `last_activity_timestamp` and `status`.
    * **`ConversationTurn`**: For every incoming user input.

**8. Dependencies:**

* **ASR Service/Library:** (e.g., Google Cloud Speech-to-Text, Azure Speech Service, local model) – for `process_audio_input`.
* **UUID Generation Library:** For generating unique identifiers.
* **Database Access Layer / ORM:** For interacting with `Device`, `User`, `Conversation`, and `ConversationTurn` data models.
* **Logging Framework:** For system logging and error reporting.

**9. Assumptions / Constraints:**

* All incoming inputs will always provide a valid `device_id`.
* Each `Device` is consistently linked to a single `User` via `owner_user_id`.
* The `INACTIVITY_THRESHOLD` is a globally configured parameter.
* ASR transcription is handled by a separate, integrated service; `InputProcessor` is responsible for calling it, not implementing the ASR itself.

---

### **Collaboration Strategy on GitHub:**

1.  **Repository Structure:** As outlined above, maintain a clear `docs/components/` directory.
2.  **Naming Convention:** Use consistent file names like `ComponentName.md` (e.g., `InputProcessor.md`).
3.  **Markdown's Simplicity:** It's plain text, so it's easy to read, edit, and understand diffs (changes) in Git. Anyone with a text editor can contribute.
4.  **GitHub Rendering:** GitHub automatically renders Markdown files beautifully in the browser, making them easy to view without needing to clone the repo or use special tools.
5.  **Pull Request Workflow:** All changes to these `md` files go through the standard Git Pull Request (PR) review process, allowing for discussion, feedback, and version history.
6.  **Embedded Diagrams:** If you have diagrams (like the one you shared), save them as `.drawio` (the source file for diagrams.net/draw.io) or export them as `.svg` (scalable vector graphics) or `.png` images, store them in a subfolder like `docs/components/images/`, and embed them directly in your Markdown using relative paths: `![Diagram Description](images/my_component_diagram.png)`.

This approach ensures that your design documentation is a living part of your project, evolves with your code, and is highly accessible and collaborative for your team.