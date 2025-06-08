# Component Specification: `brain:short_term_mem`

**1. Component Name:** `brain:short_term_mem`

**2. Conceptual Role / Nickname:** Working Memory / Scratchpad / Context Store / The "Active Thought" Register

**3. Purpose / Mission:**
The `brain:short_term_mem` is designed to provide fast, ephemeral storage and retrieval for the `ConversationContext` of all active dialogues. Its mission is to maintain the real-time state of each conversation, enabling other brain components (especially `pre-frontal_cortex` and `language_center`) to access and update dialogue information efficiently, ensuring contextual coherence throughout an interaction.

---

**4. Core Responsibilities:**

* **Context Storage:** Store the comprehensive `ConversationContext` for each active `Conversation`.
* **Rapid Access:** Provide very low-latency read and write operations for `ConversationContext` based on `conversation_id`.
* **Context Expiration:** Automatically invalidate or remove `ConversationContext` data for conversations that have been inactive beyond a predefined threshold (e.g., related to `InputProcessor`'s `INACTIVITY_THRESHOLD`).
* **Data Consistency:** Ensure that concurrent updates to a `ConversationContext` are handled gracefully, preventing data corruption or race conditions.
* **Scalability for Active Conversations:** Be able to manage context for a large number of concurrent active conversations.

---

**5. External Interfaces / APIs:**

* `get_conversation_context(conversation_id)`
* `update_conversation_context(conversation_id, new_context_data)`
* `clear_conversation_context(conversation_id)`

#### API Definition: `get_conversation_context`

* **Description:** Retrieves the current `ConversationContext` for a specified conversation.
* **Parameters:**
    * `conversation_id` (`UUID`): The unique ID of the conversation whose context is to be retrieved.
* **Returns:** (`dict` or `None`) The `ConversationContext` dictionary if found, otherwise `None`.
* **Possible Errors:**
    * `ContextNotFoundError`: If `conversation_id` does not map to an active context.

#### API Definition: `update_conversation_context`

* **Description:** Updates or creates the `ConversationContext` for a specified conversation. This is typically a full replacement or a deep merge operation of the existing context.
* **Parameters:**
    * `conversation_id` (`UUID`): The unique ID of the conversation whose context is being updated.
    * `new_context_data` (`dict`): A dictionary containing the updated or new `ConversationContext` data. This should contain the *complete* current state of the context.
* **Returns:** (`bool`) `True` if the update was successful, `False` otherwise.
* **Possible Errors:**
    * `ContextUpdateError`: If the update operation fails (e.g., database error, invalid data).

#### API Definition: `clear_conversation_context`

* **Description:** Explicitly removes the `ConversationContext` for a specified conversation. This is typically called by `pre-frontal_cortex` when a conversation officially ends or times out.
* **Parameters:**
    * `conversation_id` (`UUID`): The unique ID of the conversation whose context is to be cleared.
* **Returns:** (`bool`) `True` if context was successfully cleared, `False` if not found or error.
* **Possible Errors:**
    * `ContextRemovalError`: If the removal operation fails.

---

**6. Internal Logic / Algorithm:**

* **Underlying Store:**
    * Likely implemented using an in-memory key-value store (e.g., a Python dictionary for simple cases, or a dedicated caching solution like **Redis** for production). Redis is highly recommended for its performance, persistence options, and built-in TTL (Time-To-Live) functionality.
* **Data Structure for `ConversationContext`:**
    * The `ConversationContext` itself is a flexible dictionary that stores various elements critical to the current dialogue state. Its structure will evolve as the VA's capabilities grow.
    * **Minimum elements of `ConversationContext`:**
        * `user_id` (`UUID`): The ID of the associated user.
        * `active_goal` (`dict` or `None`): The current overarching intent/task the user is pursuing (e.g., `{'name': 'book_flight', 'status': 'slot_filling'}`).
        * `slots_filled` (`dict`): Key-value pairs of extracted or confirmed entities for the active goal (e.g., `{'origin': 'London', 'destination': 'Paris', 'date': '2025-07-15'}`).
        * `pending_questions` (`list`): List of questions the VA needs to ask the user to fill missing slots or clarify intent.
        * `recent_turns` (`list` of `dict`): A short history of the most recent user and VA utterances (e.g., last 3-5 turns), crucial for coreference resolution and maintaining flow. Each dict might contain `{'speaker': 'User/VA', 'text': '...', 'timestamp': '...'}`.
        * `current_topic` (`str` or `None`): The most recently identified topic of conversation.
        * `last_active_timestamp` (`datetime`): Timestamp of the last activity, used for expiration.
        * `system_flags` (`dict`): Any internal flags for the VA's state (e.g., `{'awaiting_confirmation': True, 'fallback_triggered': False}`).
* **Context Expiration (`TTL`):**
    * When a context is stored/updated, a Time-To-Live (TTL) is set on its entry (e.g., 5-10 minutes beyond the `INACTIVITY_THRESHOLD` from `InputProcessor`).
    * The `pre-frontal_cortex` is primarily responsible for updating `last_active_timestamp` in the context and pushing it to `short_term_mem` on every turn, which implicitly refreshes the TTL. If no updates occur for the TTL duration, the context automatically expires from `short_term_mem`.

---

**7. Data Interactions:**

* **Stores:**
    * `ConversationContext` (as defined above).
* **Accessed by:**
    * `brain:pre-frontal_cortex` (reads and writes frequently).
    * `brain:language_center` (reads for contextual NLU/NLG).
    * (Potentially other components needing immediate dialogue state, though direct access should be minimized for clarity).

---

**8. Dependencies:**

* **Caching/Key-Value Store Technology:** (e.g., Redis, in-memory dictionary for development).
* **UUID Generation Library:** (though the `conversation_id` is typically passed in from `InputProcessor`).

---

**9. Assumptions / Constraints:**

* Designed for **high-speed, ephemeral storage**. It is NOT a long-term database for historical conversations.
* Data stored in `short_term_mem` is not guaranteed to persist across system restarts unless the underlying technology (like Redis) is configured for persistence. For `ConversationContext`, this is usually acceptable, as inactive contexts expire anyway.
* The `pre-frontal_cortex` is responsible for defining the specific structure and content of `ConversationContext` and ensuring its proper update.
* Memory capacity of the underlying store must be sufficient for peak concurrent conversations.