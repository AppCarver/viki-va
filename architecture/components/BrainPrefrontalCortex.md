# Component Specification: `brain:pre-frontal_cortex`

**1. Component Name:** `brain:pre-frontal_cortex`

**2. Conceptual Role / Nickname:** Dialogue Manager / Orchestrator / Executive Function / The "Thinker"

**3. Purpose / Mission:**
The `brain:pre-frontal_cortex` is the core decision-making and control unit of the virtual assistant. Its mission is to interpret user intent in context, manage the flow of conversation, track dialogue state, fulfill user requests by coordinating with other "brain" modules and external tools, and formulate appropriate responses. It ensures coherent, goal-oriented, and personalized interactions.

---

**4. Core Responsibilities:**

* **Dialogue State Tracking:** Maintain and update the current state of the conversation (e.g., active intent, filled slots, current task, pending questions) within the `ConversationContext` (in `brain:short_term_mem`).
* **Intent Resolution & Disambiguation:** Take NLU results (intent, entities) and, using `ConversationContext`, resolve ambiguities or confirm intents.
* **Dialogue Policy Management:** Determine the next appropriate action or response based on the current dialogue state, user input, and system goals (e.g., ask clarifying questions, confirm information, execute a task, provide information).
* **External Tool/Action Orchestration:** Initiate calls to external services or tools (via an `ActionExecutor` component) to fulfill user requests (e.g., booking a flight, setting a timer, querying external APIs).
* **Knowledge Retrieval:** Coordinate with `brain:long_term_mem` to retrieve facts, summaries, or past interactions relevant to the current conversation.
* **Response Formulation & Generation Request:** Construct a structured `dialogue_act` and `response_content` for `brain:language_center`'s NLG API to generate the actual natural language output.
* **Conversation Lifecycle Management:** Handle the start, continuation, pausing, and termination of conversations (e.g., marking conversations as inactive based on timeout or explicit user command).
* **Error & Fallback Handling:** Detect and manage situations where understanding is unclear, tasks fail, or models return low confidence, providing appropriate fallback responses or re-prompting the user.
* **Output Coordination:** Receive the generated text response and coordinate its delivery back to the `Device` that initiated the turn, potentially through an intermediary `OutputManager`.

---

**5. External Interfaces / APIs:**

This component primarily has one main entry point after user input has been initially processed and understood:

* `process_dialogue_turn(turn_id, conversation_id, user_id, processed_text, nlu_results)`

#### API Definition: `process_dialogue_turn`

* **Description:** This is the core API for processing a user's turn in a dialogue. It takes the NLU results and `ConversationContext` to determine the VA's next action, orchestrate necessary steps, and formulate a response.
* **Parameters:**
    * `turn_id` (`UUID`): The ID of the current `ConversationTurn` (from `InputProcessor`).
    * `conversation_id` (`UUID`): The ID of the current `Conversation` this turn belongs to.
    * `user_id` (`UUID`): The ID of the `User` associated with this conversation.
    * `processed_text` (`str`): The normalized text of the user's utterance (from `InputProcessor`).
    * `nlu_results` (`dict`): The structured output from `brain:language_center`'s `understand_user_input` API (containing `intent`, `entities`, `sentiment`, etc.).
* **Returns:** (`dict`) A dictionary indicating the outcome of the dialogue turn processing, often including the VA's intended response:
    ```json
    {
        "success": true,
        "va_response_text": "string", // The final natural language response from the VA.
        "action_taken": "string",     // e.g., "slot_filled", "task_executed", "clarification_asked"
        "new_dialogue_state": "string", // e.g., "waiting_for_confirmation", "idle"
        "error": "string"             // (Optional) Error message if success is False.
    }
    ```
    *Note: The `va_response_text` would then be passed to the `Device` for output.*
* **Possible Errors:**
    * `DialoguePolicyError`: Failure to determine a next action.
    * `ActionExecutionError`: An orchestrated external action failed.
    * `NLGGenerationError`: Error during response generation.
    * `ContextUpdateError`: Issues saving updated `ConversationContext`.

---

**6. Internal Logic / Algorithm (Detailed Steps for `process_dialogue_turn`):**

* **Step 1: Load and Update `ConversationContext`:**
    * Load `ConversationContext` from `brain:short_term_mem` using `conversation_id` and `user_id`.
    * Update `ConversationContext` with `processed_text`, `nlu_results`, `turn_id`, and `current_timestamp`. This typically includes:
        * Storing the user's intent and extracted entities.
        * Updating relevant "slots" if a task is ongoing.
        * Logging the current turn.

* **Step 2: Dialogue Policy Engine / State Machine:**
    * Based on the current `ConversationContext` and the newly received `nlu_results`, determine the next dialogue state and the appropriate VA action. This is the core "thinking" part. Examples of logic:
        * IF `nlu_results.intent` is a new intent AND no active goal in context:
            * Set new active goal in `ConversationContext`.
            * Check if all required slots for this goal are present.
            * IF slots missing: Formulate `dialogue_act` to ask for missing slots (e.g., "ask_clarification_city").
            * ELSE (all slots present): Proceed to Step 3.
        * IF `nlu_results.intent` is a continuation of an active goal (e.g., providing a missing slot value):
            * Update relevant slots in `ConversationContext`.
            * IF all slots now present: Proceed to Step 3.
            * ELSE: Formulate `dialogue_act` to ask for remaining missing slots.
        * IF `nlu_results.intent` is a `TerminateConversation` intent:
            * Set `Conversation.status` to `inactive_user_terminated`.
            * Formulate `dialogue_act` to confirm termination (e.g., "goodbye").
        * IF `nlu_results.intent` is low confidence OR `nlu_results.entities` are ambiguous:
            * Formulate `dialogue_act` for clarification (e.g., "ask_rephrase", "ask_confirm_intent").
        * (Many other rules/policies apply here for complex dialogue, potentially using a rule engine, state charts, or a reinforcement learning model.)

* **Step 3: Action Execution (If Required):**
    * IF the current dialogue policy dictates a task execution (e.g., all slots for "book_flight" are filled):
        * Call `ActionExecutor.execute_action(goal_name, filled_slots, user_id)`.
        * Handle success/failure from `ActionExecutor`.
        * Update `ConversationContext` with action results (e.g., booking confirmation number, error message).

* **Step 4: Knowledge Retrieval (If Required):**
    * IF the `dialogue_act` requires specific facts or summaries (e.g., "inform_weather", "tell_about_user_preferences"):
        * Call `brain:long_term_mem` to `get_fact(user_id, fact_key)` or `get_summary(user_id, summary_key)`.
        * Incorporate retrieved data into `response_content`.

* **Step 5: Natural Language Generation (NLG Request):**
    * Call `brain:language_center.generate_response(dialogue_act, response_content, conversation_id, user_id)`.
    * `va_response_text` = result from `language_center`.

* **Step 6: Update Conversation State & Log VA Turn:**
    * Update `Conversation.last_activity_timestamp` to `current_timestamp`.
    * Update `Conversation.status` if necessary (e.g., to `inactive_timeout` if a decision indicates end of dialogue, or `active` if confirmed).
    * Save updated `ConversationContext` back to `brain:short_term_mem`.
    * Create a new `ConversationTurn` record for the VA's response (speaker: "VA", text: `va_response_text`, timestamp: `current_timestamp`, etc.) in `brain:conversationLog`.

---

**7. Data Interactions:**

* **Reads from:**
    * **`Conversation`**: To retrieve the current conversation's `status` and `last_activity_timestamp`.
    * **`ConversationContext`**: (via `brain:short_term_mem`) extensively, to load and understand the current dialogue state.
    * **`LongTermFact` / `LongTermSummary`**: (via `brain:long_term_mem`) to retrieve user profile data, preferences, or general knowledge for responses and task fulfillment.
* **Writes to:**
    * **`ConversationContext`**: (via `brain:short_term_mem`) to update the dialogue state (e.g., filled slots, active goals, turn history).
    * **`Conversation`**: To update its `status` (e.g., `inactive`, `active`) and `last_activity_timestamp`.
    * **`ConversationTurn`**: To log the VA's generated response.

---

**8. Dependencies:**

* **`brain:language_center`**: For NLU (`understand_user_input`) and NLG (`generate_response`).
* **`brain:short_term_mem`**: For managing `ConversationContext`.
* **`brain:long_term_mem`**: For retrieving long-term facts and summaries.
* **`ActionExecutor`**: (A new component to be defined) For executing external tasks/tool calls.
* **Logging Framework:** For system logging and error reporting.

---

**9. Assumptions / Constraints:**

* `InputProcessor` and `language_center` provide accurate and well-structured input (processed text, NLU results).
* The `ActionExecutor` correctly performs external tasks and returns reliable results.
* The dialogue policy is robust enough to handle common conversational patterns, including explicit commands, clarifications, topic changes, and error conditions.
* `ConversationContext` in `short_term_mem` is capable of storing complex dialogue state information efficiently.