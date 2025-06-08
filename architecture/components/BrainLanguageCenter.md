# Component Specification: brain:language_center

**1. Component Name:** `brain:language_center`

**2. Conceptual Role / Nickname:** Language Interpreter & Speaker / The "Linguist"

**3. Purpose / Mission:**
The `brain:language_center` is responsible for all sophisticated natural language processing tasks. Its mission is two-fold: to **understand the meaning and intent** behind user utterances (Natural Language Understanding - NLU) and to **generate coherent, contextually appropriate, and natural-sounding responses** for the virtual assistant (Natural Language Generation - NLG).

---

**4. Core Responsibilities:**

* **Natural Language Understanding (NLU):**
    * **Intent Classification:** Determine the primary goal or action the user wants to achieve (e.g., "query_weather", "set_alarm", "ask_personal_info", "terminate_conversation").
    * **Entity Extraction:** Identify and extract key pieces of information (entities) from the user's utterance that are relevant to the detected intent (e.g., city name, time, item name, recipient).
    * **Sentiment Analysis (Optional):** Assess the emotional tone of the user's input (e.g., positive, negative, neutral).
    * **Coreference Resolution (Advanced):** Identify when pronouns or phrases refer to the same entity mentioned previously in the conversation.
    * **Contextualization:** Use the `ConversationContext` (Short-Term Memory) to aid in disambiguation and understanding.

* **Natural Language Generation (NLG):**
    * **Response Formulation:** Take structured `dialogue_act`s (e.g., "confirm_task", "ask_for_clarification", "provide_info") and relevant content from the `brain:pre-frontal_cortex` and generate a natural language response.
    * **Contextual Coherence:** Ensure generated responses fit seamlessly into the ongoing `Conversation` and reference `ConversationContext` for personalization or relevant details.
    * **Tone and Style Adaptation:** Generate responses that align with the VA's persona and adapt to user's sentiment or conversational style (if designed).

---

**5. External Interfaces / APIs:**

This component exposes the following public functions:

* `understand_user_input(processed_text, conversation_id, user_id)`
* `generate_response(dialogue_act, response_content, conversation_id, user_id)`

---

#### **API Definition: `understand_user_input`**

* **Description:** Analyzes a user's processed text to determine intent, extract entities, and update the conversation context. This is the **NLU** part of the `language_center`.
* **Parameters:**
    * `processed_text` (`str`): The normalized text output from the `InputProcessor`.
    * `conversation_id` (`UUID`): The ID of the current `Conversation` this turn belongs to.
    * `user_id` (`UUID`): The ID of the `User` associated with this conversation.
* **Returns:** (`dict`) A dictionary containing the understanding results:
    ```json
    {
        "success": true,
        "intent": {
            "name": "string",       // e.g., "query_weather", "set_alarm"
            "confidence": "float"   // Confidence score (0.0 to 1.0)
        },
        "entities": [               // List of extracted entities
            {"name": "string", "value": "string", "type": "string"} // e.g., {"name": "city", "value": "London", "type": "location"}
            // ... more entities
        ],
        "sentiment": {              // Optional: Sentiment analysis result
            "polarity": "string",   // e.g., "positive", "negative", "neutral"
            "score": "float"        // Score (e.g., -1.0 to 1.0)
        },
        "error": "string"           // (Optional) Error message if not successful.
    }
    ```
* **Possible Errors:**
    * `NLUProcessingError`: General error during NLU processing.
    * `ModelLoadError`: Failure to load underlying NLU models.

---

#### API Definition: `generate_response`

* **Description:** Generates a natural language text response for the virtual assistant based on structured input from the `brain:pre-frontal_cortex`. This is the **NLG** part of the `language_center`.
* **Parameters:**
    * `dialogue_act` (`str`): A high-level description of what the VA intends to do (e.g., "confirm_booking", "ask_clarification_city", "inform_fact"). This guides the LLM/template.
    * `response_content` (`dict`): Structured data to be incorporated into the response. This is the *specific information* (e.g., `{'city': 'London', 'temperature': '20C'}` for "inform_weather").
    * `conversation_id` (`UUID`): The ID of the current `Conversation` to fetch relevant `ConversationContext`.
    * `user_id` (`UUID`): The ID of the `User` for whom the response is being generated. This is used internally by the `language_center` for context lookups (e.g., in `brain:short_term_mem`), **but user-specific conversational data (like names) should be passed in the `response_content` by the `brain:pre-frontal_cortex` for direct inclusion in the generated text.**
* **Returns:** (`dict`) A dictionary containing the generated text:
    ```json
    {
        "success": true,
        "generated_text": "string", // The final natural language response for the user.
        "error": "string"           // (Optional) Error message if not successful.
    }
    ```
* **Possible Errors:**
    * `NLGGenerationError`: General error during NLG processing.
    * `ModelLoadError`: Failure to load underlying NLG models.

---

**6. Internal Logic / Algorithm (Detailed Steps):**

#### **For `understand_user_input` (NLU):**

* **Step 1: Contextual Data Retrieval:**
    * Load `ConversationContext` from `brain:short_term_mem` using `conversation_id` and `user_id`. This provides recent turns, active goals, confirmed slots, etc.
* **Step 2: Core NLU Processing:**
    * **Intent Classification:** Feed `processed_text` and relevant `ConversationContext` (e.g., `current_topic`) to the **Intent Classifier model**.
        * Identify primary `intent_name` and `confidence_score`.
    * **Entity Extraction:** Feed `processed_text` to the **Entity Recognizer model**.
        * Extract `entities` (e.g., name, value, type).
    * **Sentiment Analysis (Optional):** Feed `processed_text` to **Sentiment Analysis model**.
        * Determine `polarity` and `score`.
* **Step 3: Contextual Refinement (Delegated):**
    * The `language_center` primarily extracts. The detailed logic of *how* these intents/entities update the `ConversationContext` (e.g., slot filling, goal tracking) and influence the next dialogue state is largely the responsibility of the `brain:pre-frontal_cortex`.
* **Step 4: Return NLU Results:**
    * Return the extracted `intent`, `entities`, and `sentiment` (if applicable).

#### **For `generate_response` (NLG):**

* **Step 1: Contextual Data Retrieval:**
    * Load `ConversationContext` from `brain:short_term_mem` using `conversation_id` and `user_id`. This is crucial for personalized or coherent responses.
    * Access `LongTermFact` or `LongTermSummary` via the `brain:pre-frontal_cortex` if the `response_content` requires facts not directly in context (e.g., "Tell me my dog's name").
* **Step 2: Prompt / Input Construction:**
    * Construct an appropriate input for the underlying **language model (LLM)** or templating engine. This input will combine:
        * The `dialogue_act` (e.g., "inform_weather").
        * The structured `response_content` (e.g., `{'city': 'London', 'temp': '20C'}`).
        * Relevant historical `ConversationTurn`s and `ConversationContext` for fluency and context.
        * VA persona guidelines.
* **Step 3: Language Generation:**
    * Call the underlying LLM or activate the appropriate templating engine with the constructed input.
    * Receive `generated_text`.
* **Step 4: Post-processing (Optional):**
    * Perform any final text clean-up, grammar correction, or tone adjustments.
* **Step 5: Log VA Turn (Delegated):**
    * The `generated_text` is typically passed back to the `brain:pre-frontal_cortex`, which then orchestrates its output via the `Device` and logs it as a new `ConversationTurn` (speaker: "VA") in `brain:conversationLog`.
* **Step 6: Return NLG Results:**
    * Return the `generated_text`.

---

**7. Data Interactions:**

* **Reads from:**
    * **`ConversationContext`**: (via `brain:short_term_mem`) extensively for both NLU and NLG.
    * **`ConversationTurn`**: (via `brain:conversationLog`) potentially for recent turn history for NLU/NLG contextualization.
* **Writes to:**
    * *(Indirectly)* The results of NLU (intent, entities) are returned, and the `brain:pre-frontal_cortex` would then use these to update `ConversationContext` (in `brain:short_term_mem`).
    * *(Indirectly)* The `generated_text` for NLG is returned, and the `brain:pre-frontal_cortex` would log it to `ConversationTurn`.

---

**8. Dependencies:**

* **NLU Model/Framework:** (e.g., Rasa NLU, spaCy, custom LLM fine-tune for NLU tasks, or commercial API like Google NLU, AWS Comprehend).
* **NLG Model/Framework:** (e.g., Large Language Model like GPT, PaLM, custom fine-tuned LLM, or template engine).
* **`brain:short_term_mem`:** For accessing `ConversationContext`.
* **`brain:long_term_mem`:** (Indirectly, usually orchestrated by `pre-frontal_cortex` for specific fact retrieval for NLG).

---

**9. Assumptions / Constraints:**

* `InputProcessor` delivers clean, normalized `processed_text`.
* The underlying NLU/NLG models are pre-trained/configured for the specific domain and language.
* The `brain:pre-frontal_cortex` is responsible for orchestrating the overall dialogue flow, including determining *when* to call `language_center`'s NLU vs. NLG APIs and *what* structured data to pass for generation.
* Error handling for model failures (e.g., low confidence, no intent detected) is critical and would result in fallback responses orchestrated by `brain:pre-frontal_cortex`.