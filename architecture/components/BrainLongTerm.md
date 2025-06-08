# Component Specification: `brain:long_term_mem`

**1. Component Name:** `brain:long_term_mem`

**2. Conceptual Role / Nickname:** Persistent Memory / Knowledge Base / Personal Dossier / The "Archivist"

**3. Purpose / Mission:**
The `brain:long_term_mem` is the persistent storage for all static, slowly changing, or historically relevant information that the virtual assistant needs to remember over time, across sessions, or for general knowledge. Its mission is to securely store and efficiently retrieve facts about users, summaries of past interactions, and potentially broader world knowledge, enabling highly personalized and informed responses.

---

**4. Core Responsibilities:**

* **Fact Storage & Retrieval (`LongTermFact`):** Store discrete, structured facts about users (e.g., name, address, preferences), system configurations, or other domain-specific constants. Provide quick lookup by `user_id` and `fact_key`.
* **Summary Storage & Retrieval (`LongTermSummary`):** Store longer-form, summarized information, such as summaries of past conversations, recurring topics, or learned insights about a user's behavior. Enable retrieval by `user_id` and `summary_key`.
* **General Knowledge Base (Optional/Via Integration):** Potentially integrate with or contain general world knowledge (e.g., factual information about geography, history, current events) that is not user-specific.
* **Data Persistence & Integrity:** Ensure that stored data is durable, consistent, and resilient to failures.
* **Querying Capabilities:** Offer flexible mechanisms to query stored information, potentially supporting complex lookups.
* **Data Security & Privacy:** Implement robust security measures to protect sensitive user data, adhering to privacy regulations.

---

**5. External Interfaces / APIs:**

* `get_fact(user_id, fact_key)`
* `set_fact(user_id, fact_key, fact_value)`
* `get_summary(user_id, summary_key)`
* `update_summary(user_id, summary_key, new_summary_content)`
* `query_general_knowledge(query_string, context_filters=None)`

#### API Definition: `get_fact`

* **Description:** Retrieves a specific discrete fact associated with a user or a general system fact.
* **Parameters:**
    * `user_id` (`UUID` or `None`): The ID of the user. Pass `None` for general (non-user-specific) facts.
    * `fact_key` (`str`): A unique identifier for the fact (e.g., "user_profile.name", "user_address", "system_config.api_key").
* **Returns:** (`any` or `None`) The value of the fact if found, otherwise `None`.
* **Possible Errors:**
    * `FactNotFoundError`: If the specified `fact_key` is not found for the given `user_id`.
    * `DatabaseError`: Issues during database interaction.

#### API Definition: `set_fact`

* **Description:** Stores or updates a specific discrete fact.
* **Parameters:**
    * `user_id` (`UUID` or `None`): The ID of the user. Pass `None` for general facts.
    * `fact_key` (`str`): A unique identifier for the fact.
    * `fact_value` (`any`): The value of the fact (can be string, number, boolean, or serializable complex object).
* **Returns:** (`bool`) `True` if the fact was successfully set/updated, `False` otherwise.
* **Possible Errors:**
    * `DatabaseError`: Issues during database interaction.
    * `InvalidFactValueError`: If `fact_value` is not a supported type or is too large.

#### API Definition: `get_summary`

* **Description:** Retrieves a specific long-form summary associated with a user.
* **Parameters:**
    * `user_id` (`UUID`): The ID of the user whose summary is to be retrieved.
    * `summary_key` (`str`): A unique identifier for the summary (e.g., "conversation_history_summary", "user_preferences_summary", "topic_interest_summary").
* **Returns:** (`str` or `dict` or `None`) The summary content if found, otherwise `None`. Summaries might be plain text or structured JSON.
* **Possible Errors:**
    * `SummaryNotFoundError`: If the specified `summary_key` is not found for the given `user_id`.
    * `DatabaseError`: Issues during database interaction.

#### API Definition: `update_summary`

* **Description:** Updates or creates a specific long-form summary. This can involve appending to, replacing, or integrating new information into an existing summary.
* **Parameters:**
    * `user_id` (`UUID`): The ID of the user whose summary is being updated.
    * `summary_key` (`str`): A unique identifier for the summary.
    * `new_summary_content` (`str` or `dict`): The new content for the summary. The `long_term_mem` or a dedicated "Summarizer" component (potentially part of `pre-frontal_cortex` or a separate sub-module) is responsible for intelligently integrating this new content into the existing summary.
* **Returns:** (`bool`) `True` if the summary was successfully updated, `False` otherwise.
* **Possible Errors:**
    * `DatabaseError`: Issues during database interaction.
    * `InvalidSummaryContentError`: If `new_summary_content` is not a supported type or format.

#### API Definition: `query_general_knowledge`

* **Description:** Queries the general knowledge base for information. This API might directly access an internal knowledge graph or act as an intermediary to an external knowledge source (e.g., a commercial search API, a specialized factual database).
* **Parameters:**
    * `query_string` (`str`): The natural language query or structured query for general knowledge.
    * `context_filters` (`dict`, optional): Additional filters or context for the query (e.g., `{'domain': 'geography', 'date_range': '2000-2010'}`).
* **Returns:** (`dict`) A dictionary containing query results (e.g., `{'answer': '...', 'source': '...', 'facts': [...]}`).
* **Possible Errors:**
    * `KnowledgeQueryError`: If the query fails or no relevant knowledge is found.
    * `ServiceUnavailableError`: If an external knowledge source is inaccessible.

---

**6. Internal Logic / Algorithm:**

* **Database Choice:** The choice of underlying database system is crucial here and depends on the scale, structure, and query patterns expected:
    * **Relational Database (e.g., PostgreSQL, MySQL):** Good for structured `LongTermFact`s with strong consistency and complex relationships.
    * **NoSQL Document Database (e.g., MongoDB, Couchbase):** Excellent for flexible schema, good for `LongTermSummary` (especially if they are JSON objects) and evolving `LongTermFact` structures.
    * **Key-Value Store (e.g., Cassandra, DynamoDB):** Very fast for simple `get_fact`/`set_fact` operations by key.
    * **Graph Database (e.g., Neo4j, Amazon Neptune):** Ideal if relationships between facts are highly important (e.g., "who knows whom," "what belongs to what").
* **Data Models:**
    * **`LongTermFact` Table/Collection:**
        * `fact_id` (`UUID`, PK)
        * `user_id` (`UUID`, FK, nullable for general facts)
        * `fact_key` (`str`, e.g., "user_profile.name", "system.config.api_key")
        * `fact_value` (`text` or `JSONB` for flexibility)
        * `created_at` (`datetime`)
        * `updated_at` (`datetime`)
    * **`LongTermSummary` Table/Collection:**
        * `summary_id` (`UUID`, PK)
        * `user_id` (`UUID`, FK)
        * `summary_key` (`str`, e.g., "conversation_history", "user_interests")
        * `summary_content` (`text` or `JSONB` for unstructured/structured summaries)
        * `created_at` (`datetime`)
        * `updated_at` (`datetime`)
* **Indexing:** Implement appropriate indexes on `user_id`, `fact_key`, and `summary_key` for efficient retrieval.
* **Summarization (Orchestrated by `pre-frontal_cortex`):** While `long_term_mem` stores summaries, the *process* of generating or updating them from raw conversation turns or other data might be orchestrated by `pre-frontal_cortex` or a dedicated "Summarizer" sub-component. `update_summary` simply receives the new content.
* **Query Parsing (for `query_general_knowledge`):** If supporting complex queries, internal logic might involve parsing `query_string` into a structured query for the underlying knowledge base.

---

**7. Data Interactions:**

* **Stores:**
    * `LongTermFact` records (user-specific facts, general facts).
    * `LongTermSummary` records (user-specific summaries of conversations/preferences).
* **Accessed by:**
    * `brain:pre-frontal_cortex` (frequently, for personalization, task fulfillment, and general knowledge).
    * `brain:language_center` (indirectly, via `pre-frontal_cortex`, to fetch data for NLG).
    * (Potentially other backend services for reporting or user management).

---

**8. Dependencies:**

* **Database System:** (e.g., PostgreSQL, MongoDB, Redis, etc.)
* **Database Client/ORM:** For interacting with the chosen database.
* **UUID Generation Library:** For primary keys.
* **Security Libraries:** For encryption, access control.
* **External Knowledge APIs:** (If `query_general_knowledge` integrates with external services).

---

**9. Assumptions / Constraints:**

* `user_id` is consistently provided for user-specific data.
* Data consistency and durability are paramount for this component.
* Scalability for potentially massive amounts of data is a key design consideration.
* Security and privacy (e.g., data encryption at rest and in transit, access controls) are critical for user-specific facts and summaries.
* The system has a clear strategy for data retention and archival.