# Components and Their Interactions: VA Proactive Message Flow

This document details the process by which the Virtual Assistant initiates a message to a user, without direct input from the user. This could be for reminders, notifications, updates, or other proactive engagements.

---

## Use Case Walkthrough: VA Initiates a Proactive Message (e.g., Reminder)

Imagine the VA needs to send a reminder to a user about an upcoming appointment.

### Step 1: Proactive Message Trigger

* **Trigger:** An event occurs that necessitates sending a proactive message. This event originates from an internal system or an external service.
    * **Examples:**
        * An internal **`Scheduler`** component (e.g., based on a user's reminder setting).
        * A **`CRM Integration Service`** (e.g., a customer service agent manually triggers a VA message).
        * An **`Event Processing Service`** (e.g., detects a user's flight has been delayed and needs a notification).
* **Component(s) Involved:** The originating service (e.g., `Scheduler`, `CRM Integration`).
* **Role:** Identifies the need for a proactive message, identifies the target user, and specifies the message's purpose and content parameters.

    * **Outgoing Data (from Initiating Service to `brain:pre-frontal_cortex`):**
        * `ProactiveMessageRequest` object containing:
            * `user_id` (UUID): The target user for the message.
            * `message_type` (Enum): e.g., `'APPOINTMENT_REMINDER'`, `'FLIGHT_DELAY_NOTIFICATION'`, `'PROMOTIONAL_MESSAGE'`.
            * `parameters` (JSONB): Data needed to compose the message (e.g., `{"appointment_time": "2025-06-07T14:00:00Z", "appointment_topic": "Dentist Checkup"}`).
            * `preferred_device_id` (Optional, UUID): If the message should go to a specific device (e.g., user's phone for SMS reminders).
            * `callback_id` (Optional, UUID): For tracking response to this specific proactive message.

**Interaction Point 1: Initiating Service -> `brain:pre-frontal_cortex`**
* **Type:** Direct API call or (more commonly for asynchronous triggers) a Message Queue event.
* **Data:** `ProactiveMessageRequest` object.
* **Expected Response:** An acknowledgment that the request was received (if synchronous) or simply placing the message on a queue (if asynchronous).

---

### Step 2: Message Content Orchestration and Generation

* **Trigger:** The `brain:pre-frontal_cortex` receives a `ProactiveMessageRequest`.
* **Component(s):** **`brain:pre-frontal_cortex`** (orchestrates), **`brain:language_center`** (NLG), **`User`** data model, **`Device`** data model.
* **Role:** The `brain:pre-frontal_cortex` takes the proactive request, retrieves necessary user and device information, determines the optimal message content, and leverages the `brain:language_center` to generate the natural language text.

    * **Incoming Data (to `brain:pre-frontal_cortex`):**
        * `ProactiveMessageRequest` object (from Initiating Service).

    * **`brain:pre-frontal_cortex` Actions:**
        1.  **Retrieve User Context:** Queries the **`User`** data model using `user_id` to retrieve user preferences (`locale`, `time_zone`), `first_name`, and general contact info.
        2.  **Determine Target Device:**
            * If `preferred_device_id` is provided, it uses that.
            * Otherwise, it queries the **`Device`** data model to find the most appropriate `device_id` for that `user_id` (e.g., most recently active chat device, or default SMS device if available).
        3.  **Retrieve Device Capabilities:** Queries the **`Device`** data model for the chosen `device_id` to get its `capabilities` (e.g., supports rich text, max characters).
        4.  **Construct NLG Request:** Based on `message_type`, `parameters`, `user` preferences, and `device_capabilities`, it forms a structured `NLG_Request` for the `brain:language_center`.
        5.  **NLG (Natural Language Generation):** Sends the `NLG_Request` to **`brain:language_center`** to generate the final message text.
        6.  **Prepare for Output:** Collects the generated `response_text` and relevant context for the `OutputManager`.

    * **Outgoing Data (from `brain:pre-frontal_cortex`):**
        * **To `User` Data Model (Read):** `user_id`. Expected: User profile data.
        * **To `Device` Data Model (Read):** `user_id` (for default device lookup) or `preferred_device_id`. Expected: Device profile data, including `capabilities`.
        * **To `brain:language_center` (API Call):**
            * `NLG_Request` object containing:
                * `user_id`, `device_id` (chosen target device)
                * `message_type` (from `ProactiveMessageRequest`)
                * `parameters` (from `ProactiveMessageRequest`)
                * `user_locale`, `user_name` (from `User` profile)
                * `device_capabilities` (from `Device` profile)
        * **To `OutputManager` (API Call or Message Queue):**
            * `RenderedResponse` object (once `brain:language_center` returns a response):
                * `user_id`, `conversation_id` (possibly new or a default for proactive), `device_id`
                * `response_text` (String): e.g., `"Hi Alice, just a reminder about your dentist checkup at 2 PM today."`
                * `response_type` (e.g., `'PROACTIVE_REMINDER'`)
                * `raw_response_content` (optional, for rich media)

---
**Note:** For proactive messages, a new `Conversation` might be created if there's no active one for that user/device, or a default/system-initiated `conversation_id` might be used. `ConversationContext` management is less critical here as it's a one-off message, but `brain:short_term_mem` could still be used to store a temporary context for any immediate follow-ups.

This sets up the message content. The final step, as with the user-initiated flow, will be the delivery via the `OutputManager`.

### Step 3: Proactive Message Delivery

* **Trigger:** The **`brain:pre-frontal_cortex`** has finalized the content of the proactive message and generated the `RenderedResponse` object.
* **Component:** **`OutputManager`**
* **Role:** Just like with user-initiated responses, the `OutputManager` is responsible for taking the VA's prepared message, adapting it to the target **`Device`**'s capabilities, and delivering it through the correct communication channel.

    * **Incoming Data (to `OutputManager`):**
        * `RenderedResponse` object (from `brain:pre-frontal_cortex`) containing:
            * `user_id` (UUID)
            * `conversation_id` (UUID - potentially a new or system-assigned one for proactive messages)
            * `device_id` (String/UUID - the target device identified in Step 2)
            * `response_text` (String): e.g., `"Hi Alice, just a reminder about your dentist checkup at 2 PM today."`
            * `response_type` (e.g., `'PROACTIVE_REMINDER'`)
            * `raw_response_content` (Optional: e.g., for rich cards, SSML for voice)

    * **`OutputManager` Actions:**
        1.  Receives the `RenderedResponse`.
        2.  (If not already provided) Retrieves the **`Device`** record using `device_id` to get its `device_type`, `capabilities`, and `configuration`.
        3.  Selects the appropriate **channel adapter** based on the `device_type` (e.g., SMS Gateway Adapter, Mobile App Push Notification Adapter).
        4.  **Formats the Message:** Transforms the `response_text` and any `raw_response_content` into the specific format required by the chosen channel adapter and the device's capabilities.
        5.  Sends the formatted message payload to the external communication channel via its adapter.
        6.  Logs the VA's proactive message as a new **`ConversationTurn`** within the `brain:conversationLog`.

    * **Outgoing Data (from `OutputManager`):**
        * **To Data Store (Reads):** Directly interacts with the **`Device`** data model to get device-specific information.
        * **To External Communication Channel (API Call):** Sends the final, formatted message payload (e.g., HTTP POST request for a push notification, SMS message via a gateway).
        * **To `brain:conversationLog` (API Call/Message Queue):**
            * `ConversationTurn` record for the VA's proactive message:
                * `conversation_id`, `user_id`, `device_id`, `turn_number`
                * `speaker_type`: `'VA'`
                * `text_content`: `"Hi Alice, just a reminder about your dentist checkup at 2 PM today."`
                * `timestamp`, `metadata` (e.g., `{"proactive_message_type": "APPOINTMENT_REMINDER"}`)