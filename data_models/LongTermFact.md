# Data Model: LongTermFact

**1. Data Model Name:** `LongTermFact`

**2. Purpose / Description:**
A `LongTermFact` represents a discrete, structured, and persistently stored piece of information about a user or a general knowledge point acquired by the Virtual Assistant. Unlike the transient `ConversationContext`, facts in long-term memory are designed for enduring recall, personalization across sessions, and building a cumulative knowledge base. They are typically extracted from past conversations, explicit user profile updates, or external knowledge sources.

This data model is primarily managed and utilized by the `brain:long_term_mem` component.

---

**3. Key Fields / Schema:**

* **`fact_id`** (UUID, **Primary Key**):
    * A unique identifier for this specific `LongTermFact` record.
* **`user_id`** (UUID, **Indexed**, Optional):
    * The unique identifier of the user to whom this fact pertains. If the fact is general knowledge (not user-specific), this field may be null.
* **`fact_type`** (String / Enum, **Indexed**):
    * Categorization of the fact's nature, enabling efficient querying and application.
    * **Examples:**
        * `'USER_PREFERENCE'` (e.g., favorite food, preferred communication channel)
        * `'DEMOGRAPHIC'` (e.g., age range, city, occupation)
        * `'HISTORICAL_ACTION'` (e.g., last product purchased, last service requested)
        * `'KNOWLEDGE_POINT'` (e.g., "VA can reset passwords", "opening hours of store X")
        * `'SYSTEM_STATUS'` (e.g., "current system outage for service Y")
        * `'CONTACT_INFO'` (e.g., preferred email, phone number)
* **`key`** (String, **Indexed**):
    * A concise, standardized name for the specific piece of information.
    * **Examples:** `'favorite_color'`, `'delivery_address_line1'`, `'last_order_id'`, `'password_reset_capability'`.
* **`value`** (JSONB / Any Type, **Indexed if searchable**):
    * The actual data value of the fact. This can be a simple string, number, boolean, array, or a complex JSON object for structured data.
    * **Examples:** `"blue"`, `"123 Main St"`, `{"product_id": "ABC123", "quantity": 2}`, `true`.
* **`source_conversation_id`** (UUID, Optional, **Indexed**):
    * The ID of the specific `Conversation` (from `brain:conversationLog`) from which this fact was extracted or where it was last confirmed. Useful for auditing and debugging.
* **`extracted_timestamp`** (Datetime):
    * The timestamp when this fact was initially extracted or recorded into long-term memory.
* **`last_updated_timestamp`** (Datetime):
    * The timestamp when this fact was last confirmed or modified.
* **`confidence_score`** (Float, Optional):
    * A score (0.0 to 1.0) indicating the VA's confidence in the accuracy of this fact, especially relevant for facts derived via NLP.
* **`valid_until`** (Datetime, Optional):
    * For facts that have a limited lifespan (e.g., a promotional offer, temporary status). Facts can be automatically expired by `brain:long_term_mem`.
* **`status`** (Enum: `'active'`, `'inactive'`, `'deprecated'`, Optional):
    * Manages the lifecycle of the fact. `'inactive'` might mean it's no longer current, `'deprecated'` might mean it's superseded by a new fact.

---

**4. Relationships to Other Components and Data Models:**

* **Managed by `brain:long_term_mem`:** This component is the primary responsible party for storing, updating, retrieving, and managing the lifecycle of `LongTermFact` records.
* **Accessed by `brain:pre-frontal_cortex`:** `brain:pre-frontal_cortex` queries `brain:long_term_mem` to retrieve relevant `LongTermFact`s to personalize responses, inform dialogue management, and utilize knowledge.
* **Derived from `ConversationTurn` and `Conversation`:** Facts are often extracted from the raw textual content of `ConversationTurn` records, typically processed by `brain:language_center` (or a specialized NLP sub-service within `long_term_mem`).
* **Supplements `User` data:** `LongTermFact` can store dynamic user preferences and historical interactions that might not fit into a static `User` profile schema.
* **Influenced by `ActionExecutor` (Indirectly):** Outcomes of `ActionExecutor` calls (e.g., "order placed successfully") might generate new `LongTermFact`s.

---

**5. Lifecycle:**

1.  **Extraction/Creation:** `LongTermFact`s are primarily created via background processes within `brain:long_term_mem`, which analyzes `ConversationTurn` data (often with help from `brain:language_center`) or by direct integration from external user profile updates.
2.  **Retrieval:** `brain:pre-frontal_cortex` queries `brain:long_term_mem` to retrieve relevant facts based on `user_id`, `fact_type`, or semantic relevance.
3.  **Update/Validation:** Facts can be updated or re-validated by subsequent conversations or new external data. If a user states a new preference, the old fact might be updated or marked inactive.
4.  **Expiration/Deprecation:** Facts can be automatically expired based on `valid_until` or manually deprecated if no longer relevant or superseded.

---