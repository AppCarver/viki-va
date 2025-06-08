# Components and Their Interactions: Background Process - Long-Term Memory Management

This document details an asynchronous background process vital for the Virtual Assistant's ability to learn, personalize, and efficiently manage user context over extended periods. It focuses on how past conversation data is transformed into concise summaries and actionable long-term facts.

---

## Use Case Walkthrough: Archiving and Summarizing Past Conversations

Imagine a user has had a long conversation with the VA, or several short ones over a period. This process ensures relevant information from these interactions is condensed and stored for future recall by `brain:pre-frontal_cortex`.

### Step 1: Trigger for Archival/Summarization

* **Trigger:** This process is typically initiated by an asynchronous event or a scheduled job.
    * **Examples of Triggers:**
        * **`Conversation End Event`**: When a conversation is explicitly ended or times out (e.g., 30 minutes of inactivity). The `InputProcessor` or a dedicated `ConversationManager` component might emit this event.
        * **`Scheduled Job`**: A nightly or hourly batch process that scans for conversations older than a certain threshold or those marked for archival.
        * **`Memory Pressure Event`**: If `brain:short_term_mem` is nearing capacity, it might trigger archival of older contexts.
* **Component(s) Involved:**
    * **`ConversationManager`** (conceptual component that might manage conversation lifecycle and emit events)
    * **`Scheduler Service`** (conceptual component for batch jobs)
    * **`brain:long_term_mem`** (as the primary recipient of the trigger, initiating its internal process)

    * **Outgoing Data (from Triggering Service to `brain:long_term_mem`'s queue):**
        * `ArchivalRequest` object containing:
            * `conversation_id` (UUID) or `user_id` (UUID) if summarizing across multiple conversations.
            * `trigger_type` (Enum: `'CONVERSATION_END'`, `'SCHEDULED_BATCH'`).
            * `timestamp`

**Interaction Point 1: Triggering Service -> `brain:long_term_mem` (via Message Queue)**
* **Type:** Asynchronous Message Queue (e.g., Kafka, RabbitMQ, SQS). This is crucial to avoid blocking real-time VA interactions.
* **Data:** `ArchivalRequest` object.
* **Expected Response:** None (fire-and-forget for the trigger, `brain:long_term_mem` handles asynchronously).

---

### Step 2: Conversation Data Retrieval and Processing

* **Trigger:** The `brain:long_term_mem` service consumes an `ArchivalRequest` from its message queue.
* **Component(s):** **`brain:long_term_mem`** (orchestrates), **`ConversationTurn`** data model, **`brain:language_center`** (for summarization/fact extraction), **`brain:short_term_mem`** (for context removal).
* **Role:** `brain:long_term_mem` retrieves the full conversation history, processes it to extract or summarize key information, and prepares this data for storage.

    * **Incoming Data (to `brain:long_term_mem` service instance):**
        * `ArchivalRequest` object (from its queue).

    * **`brain:long_term_mem` Actions:**
        1.  **Retrieve Conversation Turns:** Queries the **`ConversationTurn`** data store (via `conversation_id`) to fetch all turns of the conversation to be archived. This might involve fetching hundreds or thousands of `ConversationTurn` records.
        2.  **Initial Data Aggregation:** Aggregates the `text_content` from all relevant `ConversationTurn`s for processing.
        3.  **Fact Extraction / Summarization / Embedding Generation:**
            * Sends the aggregated text to **`brain:language_center`** (or a dedicated sub-service within `long_term_mem` specialized in background NLP) for:
                * **Fact Extraction:** Identifying specific, structured pieces of information (e.g., user's new address, stated preferences, common topics).
                * **Summarization:** Generating a concise narrative summary of the conversation.
                * **Embedding Generation:** Creating vector embeddings of the conversation content for semantic search.
            * This is an intensive NLP process and might be delegated to a specialized ML inference service.
        4.  **Structure `LongTermFact` & `LongTermSummary`:** Organizes the extracted facts, summaries, and embeddings into the schema of the **`LongTermFact`** and **`LongTermSummary`** data models.
        5.  **Clean Short-Term Memory (Optional):** Once successfully processed for long-term storage, the `brain:long_term_mem` might send a message to `brain:short_term_mem` to remove the corresponding `ConversationContext` to free up resources.
        6.  **Mark for Archival:** Update the `Conversation` and/or `ConversationTurn` records in `brain:conversationLog` to mark them as 'archived' or 'processed for LTM', ensuring they aren't processed again.

    * **Outgoing Data (from `brain:long_term_mem` service instance):**
        * **To `ConversationTurn` Data Store (Read & Write):** `conversation_id` to retrieve turns. Updates status (e.g., `is_archived: true`).
        * **To `brain:language_center` (API Call or Message Queue):**
            * `NLP_Processing_Request` object containing:
                * `user_id`, `conversation_id`
                * `raw_conversation_text` (concatenated turns).
                * `processing_tasks` (Enum: `'FACT_EXTRACTION'`, `'SUMMARIZATION'`, `'EMBEDDING_GEN'`).
        * **To `brain:short_term_mem` (API Call):**
            * `Eviction_Request` object: `conversation_id` (to remove context).

**Interaction Point 1: `brain:long_term_mem` <> `ConversationTurn` Data Store**
* **Type:** Database/Datastore interactions (Reads for turns, Writes for status updates).
* **Data:** `ConversationTurn` records.

**Interaction Point 2: `brain:long_term_mem` -> `brain:language_center` (for NLP)**
* **Type:** Asynchronous API call or Message Queue. Could involve large data payloads.
* **Data:** Raw conversation text, processing instructions.
* **Expected Response:** `NLP_Result` (extracted facts, generated summary, embeddings).

**Interaction Point 3: `brain:long_term_mem` -> `brain:short_term_mem` (Eviction)**
* **Type:** Direct API Call.
* **Data:** `conversation_id`.
* **Expected Response:** Confirmation of context removal.

---

### Step 3: Persistence of Long-Term Memory Data

* **Trigger:** The `brain:long_term_mem` service has successfully processed the conversation and received NLP results.
* **Component:** **`brain:long_term_mem`**
* **Role:** Persists the newly generated `LongTermFact`s, `LongTermSummary`, and embeddings into its dedicated data store for efficient retrieval in future conversations.

    * **Incoming Data (to `brain:long_term_mem` service instance):**
        * Processed facts, summaries, and embeddings (from internal processing and `brain:language_center`'s response).

    * **`brain:long_term_mem` Actions:**
        1.  Stores the structured `LongTermFact` records (e.g., `{"fact_type": "user_preference", "key": "favorite_food", "value": "pizza", "user_id": "..."}`).
        2.  Stores the `LongTermSummary` record (e.g., `{"summary_text": "User discussed vacation plans and favorite food", "user_id": "..."}`).
        3.  Stores the embeddings (e.g., in a vector database).
        4.  Confirms successful persistence.

    * **Outgoing Data (from `brain:long_term_mem` service instance):**
        * **To `LongTermFact` and `LongTermSummary` Data Stores (Writes):** Structured `LongTermFact` and `LongTermSummary` records.

**Interaction Point 1: `brain:long_term_mem` <> `LongTermFact`/`LongTermSummary` Data Stores**
* **Type:** Database/Datastore interactions (Writes/Inserts).
* **Data:** `LongTermFact` and `LongTermSummary` records.