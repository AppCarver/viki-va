# Data Model: `Device`

**1. Data Model Name:** `Device`

**2. Conceptual Role / Nickname:** Communication Channel / Endpoint Configuration / Device Profile

**3. Purpose / Mission:**
The `Device` data model stores persistent information about each specific communication channel or device instance through which a `User` interacts with the virtual assistant. Its mission is to enable the `InputProcessor` to correctly interpret incoming messages and the `OutputManager` to accurately format and deliver responses, ensuring compatibility with the diverse capabilities of various platforms (e.g., text-only SMS, rich-media chat apps, voice-only smart speakers).

---

**4. Schema Definition:**

This model defines the core attributes and configurations for a particular device or communication channel.

* **`device_id`** (`String` or `UUID`, Primary Key)
    * **Description:** A unique identifier for this specific device instance or communication channel. This could be a UUID generated internally, or a unique ID provided by the platform (e.g., an Alexa device ID, a specific chat session ID, a phone number used for SMS).
    * **Example:** `"alexa-echo-12345"`, `"whatsapp-instance-abcdef"`, `"webchat-session-xyz"`
* **`device_type`** (`Enum: 'SMS', 'WEB_CHAT', 'WEB_VOICE', 'SMART_SPEAKER_ALEXA', 'SMART_SPEAKER_GOOGLE', 'MOBILE_APP', 'EMAIL', 'PHONE_CALL_IVR', 'CUSTOM_API', 'ADMIN_CONSOLE'`)
    * **Description:** The broad category or type of communication channel/device. This dictates the general capabilities and required adapters.
    * **Example:** `'SMART_SPEAKER_ALEXA'`, `'WEB_CHAT'`
* **`channel_identifier`** (`String`, Indexed, Unique within `device_type`)
    * **Description:** A more specific identifier within the `device_type`. For SMS, it might be the phone number. For web chat, a unique session ID. For smart speakers, the platform's device ID. This field helps map incoming messages to a known device.
    * **Example:** `"+1-555-987-6543"` (for SMS), `"amzn1.ask.device.ABCDEFG"` (for Alexa), `"websocket-client-123"` (for Web Chat)
* **`user_id`** (`UUID`, Foreign Key to `User` model, Nullable, Indexed)
    * **Description:** The `user_id` of the primary or last known `User` associated with this device. While a device might be used by multiple users (e.g., a family smart speaker), this can help in initial user identification or defaulting. Can be `null` for public/shared devices or where user is identified via `UserExternalIdentity`.
    * **Example:** `7890abcdef-1234-5678-90ab-cdef12345678`
* **`capabilities`** (`JSONB`)
    * **Description:** A structured dictionary outlining the specific technical capabilities of this device/channel. This is critical for content adaptation.
    * **Examples:**
        * `{"supports_tts": true, "tts_formats": ["mp3", "opus"]}`
        * `{"supports_rich_text": true, "max_char_length": 1600, "supported_media_types": ["image", "video", "audio"], "supports_buttons": true, "button_limit": 5}`
        * `{"input_mode": "voice_only", "output_mode": "voice_only"}`
* **`configuration`** (`JSONB`, Sensitive/Encrypted)
    * **Description:** Contains sensitive or specific configuration details needed for interacting with the external platform API for this device/channel. This might include API keys, endpoint URLs, webhooks, or references to secrets in a dedicated secret manager. **This data must be secured (encrypted or pointers to secret manager).**
    * **Example:** `{"api_endpoint": "https://api.chatapp.com/v1", "auth_token_ref": "secret_manager_chatapp_token_123", "webhook_secret": "secret_manager_webhook_secret_abc"}`
* **`created_at`** (`DateTime`, Indexed)
    * **Description:** The timestamp when this device record was first registered or detected.
    * **Example:** `2024-03-01T09:00:00Z`
* **`last_active_at`** (`DateTime`, Indexed)
    * **Description:** The timestamp of the most recent interaction with this device. Useful for activity tracking and cleanup.
    * **Example:** `2025-06-06T17:35:00Z`
* **`status`** (`Enum: 'active', 'inactive', 'disabled', 'retired'`)
    * **Description:** The current operational status of the device/channel.
        * `active`: Currently in use.
        * `inactive`: No recent activity, but still considered valid.
        * `disabled`: Temporarily or permanently disabled by an administrator.
        * `retired`: No longer supported or phased out.
    * **Default:** `active`
* **`metadata`** (`JSONB` or `Text`, Optional)
    * **Description:** A flexible field for storing any additional, unstructured or custom properties about the device.
    * **Example:** `{"firmware_version": "1.2.3", "battery_level": 85}`

---

**5. Relationships:**

* **Many-to-One (`Device` to `User`):**
    * Multiple `Device` records can be associated with a single `User` (a user can have many devices). The `user_id` field captures this relationship.
* **One-to-Many (`Device` to `Conversation`):**
    * A single `Device` can be the origin or target for many `Conversation` sessions. `Conversation.device_id` links to this table.
* **One-to-Many (`Device` to `ConversationTurn`):**
    * Individual `ConversationTurn` records are also linked to a `Device` via `ConversationTurn.device_id`.

---

**6. Lifecycle Considerations:**

* **Creation:**
    * A new `Device` record is typically created when the **`InputProcessor`** detects interaction from a previously unknown `channel_identifier` for a `device_type`.
    * Can also be created via administrative tools for pre-configured channels (e.g., setting up a new Twilio number).
* **Updates:**
    * `last_active_at` is updated by `InputProcessor` (on incoming messages) and `OutputManager` (on successful delivery).
    * `capabilities` or `configuration` might be updated if a platform changes its API or features.
* **Deletion:** Devices are typically disabled or retired rather than deleted, especially if they are used for auditing. Deletion would occur for truly defunct or test devices.

---

**7. Accessed By / Used By:**

* **`InputProcessor`:** Uses `device_id` and `channel_identifier` to identify incoming messages and associate them with a known device and user.
* **`OutputManager`:** Critically relies on `device_type`, `capabilities`, and `configuration` to correctly format and deliver VA responses to the appropriate channel/device.
* **`brain:pre-frontal_cortex`:** May consult `capabilities` when planning responses (e.g., "Can this device show a rich UI?").
* **User Management / Device Management Services:** For administrative tasks like enabling/disabling devices or viewing usage.

---

**8. Assumptions / Constraints:**

* `device_id` is the definitive, stable identifier for a particular device instance or channel.
* The combination of `(device_type, channel_identifier)` is unique, allowing identification of a specific communication endpoint.
* **Sensitive `configuration` data is securely stored and accessed**, ideally via a dedicated secret management system.
* `capabilities` accurately reflect the device's current technical features for content rendering and interaction.