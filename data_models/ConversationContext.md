# Data Model: ConversationContext

**1. Data Model Name:** `ConversationContext`

**2. Purpose / Description:**
The `ConversationContext` represents the dynamic, mutable, and short-lived state of an ongoing conversation between a user and the Virtual Assistant. It's the "working memory" that allows the VA to maintain coherence, track user intent progression, remember extracted entities, and manage dialogue turns within a single session. This context is crucial for multi-turn interactions, disambiguation, and personalized responses in the immediate conversation.

It is primarily managed by the `brain:short_term_mem` component, which ensures fast access and eventual eviction.

---

**3. Key Fields / Schema:**

The `ConversationContext` is typically stored as a structured object (e.g., JSONB in a database, or a Map in a cache) with the following key fields:

* **`conversation_id`** (UUID, **Primary Key/Identifier**):
    * A unique identifier for the conversation this context belongs to. Links directly to the `Conversation` data model.
* **`user_id`** (UUID, **Indexed**):
    * The unique identifier of the user involved in this conversation.
* **`last_active_timestamp`** (Datetime, **Indexed for Eviction**):
    * Timestamp of the last activity (user message or VA response) in this conversation. Used by `brain:short_term_mem` to identify inactive contexts for eviction.
* **`current_intent`** (String / Enum):
    * The VA's current understanding of the overarching user goal or primary intent in the ongoing turn or dialogue (e.g., "book_flight", "check_order_status", "ask_question").
* **`extracted_entities`** (JSONB / Map<String, Any>):
    * A collection of key-value pairs representing entities (named or otherwise) extracted from the current or previous user utterances. These are typically raw values (e.g., `{"city": "London", "date": "tomorrow", "product_type": "laptop"}`).
* **`dialogue_state`** (JSONB / Map<String, Any>):
    * Tracks the progress of multi-turn dialogues or forms. This is crucial for guiding the conversation.
    * Example: `{"booking_flight": {"step": "destination_prompted", "origin": "NYC", "passengers_count": 2}}`
    * Example: `{"order_status_query": {"awaiting_order_id": true}}`
* **`slots_filled`** (JSONB / Map<String, Any>):
    * Specifically tracks which required "slots" (parameters) for a given intent or action have been successfully filled. This is often derived from `extracted_entities` but with a focus on completeness for an action.
    * Example: `{"destination": "London", "date": null, "airline": "British Airways"}`
* **`user_utterance_history`** (Array of Strings, limited length):
    * A short, chronological log of the user's most recent raw messages. Used for quick recall or disambiguation.
* **`system_utterance_history`** (Array of Strings, limited length):
    * A short, chronological log of the VA's most recent responses. Used for context or to avoid repetition.
* **`previous_actions`** (Array of Strings / Enums, limited length):
    * A short log of the last few significant actions the VA attempted or executed (e.g., "api_call_weather_successful", "database_lookup_failed").
* **`flags`** (JSONB / Map<String, Boolean>):
    * Boolean flags indicating specific temporary states in the conversation (e.g., `{"awaiting_confirmation": true, "escalation_triggered": false}`).
* **`metadata`** (JSONB / Map<String, Any>, Optional):
    * Any other temporary, arbitrary data that needs to be stored for the current conversation's context.

---

**4. Relationships to Other Components and Data Models:**

* **Managed by `brain:short_term_mem`:** This component is the sole owner and manager of `ConversationContext` objects, providing fast read/write access.
* **Used by `brain:pre-frontal_cortex`:** The primary consumer and updater of `ConversationContext`. It reads the context to understand the current state and updates it based on NLU results, dialogue management decisions, and action outcomes.
* **Used by `brain:language_center`:** May access `extracted_entities` or `dialogue_state` for NLU refinement or to inform NLG.
* **Links to `Conversation`:** The `conversation_id` is the direct link to the `Conversation` record in `brain:conversationLog`, though `ConversationContext` itself is ephemeral.
* **Influences `ActionExecutor`:** The `dialogue_state` and `slots_filled` directly inform what actions `ActionExecutor` should attempt.
* **Influenced by `InputProcessor`:** `InputProcessor` fetches existing context or initiates a new one for incoming messages.
* **Influences `brain:long_term_mem` (Indirectly):** When a context is evicted, `brain:long_term_mem` often processes the full `Conversation` history (from `brain:conversationLog`) to create `LongTermFact`s and `LongTermSummary` entries.

---

**5. Lifecycle:**

1.  **Creation:** A new `ConversationContext` is initialized (typically by `brain:short_term_mem`) when the `InputProcessor` receives the first message for a new `conversation_id`.
2.  **Update:** It is continuously updated by `brain:pre-frontal_cortex` after each turn of the conversation, reflecting new information, state changes, and VA actions.
3.  **Eviction/Expiration:** After a defined period of inactivity (e.g., 30 minutes, 2 hours), `brain:short_term_mem` will automatically evict the `ConversationContext` to free up resources. This eviction often triggers a background process in `brain:long_term_mem` to archive the full conversation from `brain:conversationLog`.

---