# Data Model: `Conversation`

**1. Data Model Name:** `Conversation`

**2. Conceptual Role / Nickname:** Dialogue Session Record / Interaction Container

**3. Purpose / Mission:**
The `Conversation` data model serves as the central ledger for each unique, continuous dialogue session between a `User` and the virtual assistant. Its mission is to track the essential metadata, status, and lifecycle of a single interaction, providing the context for all `ConversationTurn`s and linking to the associated `User` and `Device`.

---

**4. Schema Definition:**

This model defines the core attributes and structure of a single conversation session.

* **`conversation_id`** (`UUID`, Primary Key)
    * **Description:** A unique identifier for this specific conversation session. This ID is generated at the start of a new session.
    * **Example:** `a1b2c3d4-e5f6-7890-1234-567890abcdef`
* **`user_id`** (`UUID`, Foreign Key to `User` model)
    * **Description:** The unique identifier of the `User` involved in this conversation.
    * **Example:** `user-alpha-123`
* **`device_id`** (`String` or `UUID`, Foreign Key to `Device` model, Nullable)
    * **Description:** The identifier of the specific `Device` from which the conversation was initiated or is primarily ongoing. Can be `null` if the conversation is initiated by the VA (e.g., proactive notification).
    * **Example:** `whatsapp-channel-12345`, `alexa-device-abc`
* **`start_timestamp`** (`DateTime`, Indexed)
    * **Description:** The timestamp when the conversation session officially began.
    * **Example:** `2025-06-06T10:00:00Z`
* **`last_activity_timestamp`** (`DateTime`, Indexed)
    * **Description:** The timestamp of the most recent interaction (either user input or VA response) within this conversation. Used for tracking inactivity and session expiration.
    * **Example:** `2025-06-06T10:05:30Z`
* **`status`** (`Enum: 'active', 'inactive_timeout', 'inactive_user_terminated', 'inactive_system_terminated', 'archived'`)
    * **Description:** The current state of the conversation session.
        * `active`: Conversation is ongoing and recently active.
        * `inactive_timeout`: Session ended due to user inactivity.
        * `inactive_user_terminated`: User explicitly ended the conversation (e.g., "goodbye").
        * `inactive_system_terminated`: System-initiated termination (e.g., task completed, error).
        * `archived`: Conversation data moved to long-term storage or summary.
    * **Default:** `active`
* **`topic`** (`String`, Optional)
    * **Description:** A high-level descriptor of the main subject or domain of the conversation (e.g., "flight booking", "weather inquiry", "smart home control"). Can be updated throughout the conversation.
    * **Example:** `"flight_booking"`
* **`current_goal`** (`JSONB` or `Text`, Optional)
    * **Description:** A snapshot or simplified representation of the `active_goal` from the `ConversationContext` at the last major update. Useful for reporting or initial context loading without fetching full `ConversationContext`.
    * **Example:** `{"name": "book_flight", "status": "slot_filling", "departure_city_filled": true}`
* **`metadata`** (`JSONB` or `Text`, Optional)
    * **Description:** A flexible field for storing any additional, unstructured metadata about the conversation that doesn't fit into other fields.
    * **Example:** `{"source_channel": "WhatsApp", "initial_utterance_length": 25}`

---

**5. Relationships:**

* **One-to-Many (`Conversation` to `ConversationTurn`):**
    * A single `Conversation` session comprises multiple `ConversationTurn` records (one for each user input and VA response).
* **Many-to-One (`Conversation` to `User`):**
    * Multiple `Conversation` sessions can belong to a single `User`.
* **Many-to-One (`Conversation` to `Device`):**
    * Multiple `Conversation` sessions can originate from a single `Device` (e.g., same phone number).

---

**6. Lifecycle Considerations:**

* **Creation:** A new `Conversation` record is typically created by the **`InputProcessor`** when a new user interaction is detected that doesn't belong to an existing active conversation.
* **Updates:** The `last_activity_timestamp` and `status` fields are primarily updated by the **`brain:pre-frontal_cortex`** as it processes each turn. The `topic` and `current_goal` may also be updated by `pre-frontal_cortex`.
* **Archival/Deletion:** Conversations with an `inactive_` status are candidates for eventual archival or deletion, managed by background processes or a dedicated **Data Lifecycle Management** service (possibly part of `brain:long_term_mem`'s extended responsibilities or a separate system concern). This ensures that `brain:short_term_mem` doesn't get overloaded with stale contexts and that historical data is managed.

---

**7. Accessed By / Used By:**

* **`InputProcessor`:** Creates new `Conversation` records.
* **`brain:pre-frontal_cortex`:** Reads `status`, `last_activity_timestamp`, `topic`, `current_goal`; updates `status`, `last_activity_timestamp`, `topic`, `current_goal`.
* **`brain:short_term_mem`:** Uses `conversation_id` as the primary key to store and retrieve `ConversationContext`.
* **`brain:conversationLog` (conceptual/upcoming):** Logs `ConversationTurn`s, which are linked to a `Conversation`.
* **Reporting/Analytics Services:** (External to current scope) Would query `Conversation` data for usage statistics.

---

**8. Assumptions / Constraints:**

* `conversation_id` is globally unique and immutable once created.
* The `user_id` and `device_id` are consistently identifiable and valid.
* `status` transitions are managed coherently (e.g., an `active` conversation doesn't directly jump to `archived` without an `inactive_` state).
* The system has a defined inactivity timeout after which a conversation transitions to `inactive_timeout`.

---

How does this look for the `Conversation` data model? We can move on to `ConversationTurn`, `User`, or `Device` next, or refine this one further.