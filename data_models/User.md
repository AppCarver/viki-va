# Data Model: `User` (Revised)

**1. Data Model Name:** `User`

**2. Conceptual Role / Nickname:** User Profile / Customer Record / Individual Identity

**3. Purpose / Mission:**
The `User` data model stores unique and persistent information about each individual interacting with the virtual assistant. Its mission is to provide a central identity for users, enable personalization across different conversations and devices, and serve as the anchor for all user-specific data within the system (like preferences and historical interactions). This model now leverages the `UserExternalIdentity` table for managing multiple external system identifiers.

---

**4. Schema Definition:**

This model defines the core attributes and structure of a single user's profile.

* **`user_id`** (`UUID`, Primary Key)
    * **Description:** A globally unique identifier for this user within the virtual assistant system. This is the primary key used to link all user-specific data (conversations, preferences, facts).
    * **Example:** `7890abcdef-1234-5678-90ab-cdef12345678`
* **`first_name`** (`String`, Optional)
    * **Description:** The user's given name. Useful for personalization (e.g., "Hello, [First Name]!").
    * **Example:** `"Alice"`
* **`last_name`** (`String`, Optional)
    * **Description:** The user's family name.
    * **Example:** `"Smith"`
* **`email`** (`String`, Optional, Indexed, Unique)
    * **Description:** The user's primary email address. Can be used for account management, notifications, or identification. Should be unique if provided.
    * **Example:** `"alice.smith@example.com"`
* **`phone_number`** (`String`, Optional, Indexed, Unique)
    * **Description:** The user's primary phone number. Can be used for SMS notifications, voice interactions, or identification. Should be unique if provided.
    * **Example:** `"+1-555-123-4567"`
* **`created_at`** (`DateTime`, Indexed)
    * **Description:** The timestamp when this user record was first created (i.e., when they first interacted with the VA).
    * **Example:** `2024-01-15T08:30:00Z`
* **`last_active_at`** (`DateTime`, Indexed)
    * **Description:** The timestamp of the user's most recent interaction with the virtual assistant. Useful for activity tracking and retention policies.
    * **Example:** `2025-06-06T17:20:00Z`
* **`time_zone`** (`String`, Optional)
    * **Description:** The user's preferred time zone (e.g., `America/Chicago`, `Europe/London`). Important for time-sensitive actions like setting reminders or providing localized information.
    * **Example:** `"America/Chicago"`
* **`locale`** (`String`, Optional)
    * **Description:** The user's preferred language and regional settings (e.g., `en-US`, `es-MX`, `fr-CA`). Crucial for `brain:language_center`'s NLG and I18n.
    * **Example:** `"en-US"`
* **`status`** (`Enum: 'active', 'inactive', 'suspended', 'deleted'`)
    * **Description:** The current operational status of the user account.
        * `active`: The user is actively interacting.
        * `inactive`: No recent activity, but account is still valid.
        * `suspended`: Account temporarily disabled.
        * `deleted`: User account and associated data have been (or are being) permanently removed.
    * **Default:** `active`
* **`metadata`** (`JSONB` or `Text`, Optional)
    * **Description:** A flexible field for storing any additional, unstructured or custom properties about the user that don't fit into the predefined schema.
    * **Example:** `{"customer_segment": "premium", "signed_up_for_newsletter": true}`

---

**5. Relationships:**

* **One-to-Many (`User` to `Conversation`):**
    * A single `User` can have multiple `Conversation` sessions over time.
* **One-to-Many (`User` to `Device`):**
    * A single `User` can interact with the VA through multiple `Device`s (e.g., their phone, a smart speaker, a web browser).
* **One-to-Many (`User` to `LongTermFact` / `LongTermSummary`):**
    * Many user-specific facts and summaries stored in `brain:long_term_mem` are directly linked to a `User` via `user_id`.
* **One-to-Many (`User` to `UserExternalIdentity`):**
    * A single `User` can be linked to multiple `UserExternalIdentity` records, each representing their ID in a different external system. This relationship is managed through the `UserExternalIdentity` table.

---

**6. Lifecycle Considerations:**

* **Creation:** A new `User` record is typically created by the **`InputProcessor`** upon the first detected interaction from a unique individual that cannot be linked to an existing `User` record via any known `UserExternalIdentity`.
* **Updates:**
    * `last_active_at` is updated by the **`brain:pre-frontal_cortex`** with each significant user interaction.
    * Other fields (name, email, preferences, locale) can be updated through explicit user commands handled by `pre-frontal_cortex` (which then uses `ActionExecutor` to persist changes) or via external user management systems.
* **Deletion:** User records are deleted according to user requests (e.g., "delete my data"), data retention policies, or legal compliance requirements (e.g., GDPR "right to be forgotten"). This process must trigger the deletion or anonymization of all associated user data, including related `Conversation`s, `ConversationTurn`s, `LongTermFact`s, `LongTermSummary`s, and all linked `UserExternalIdentity` records.

---

**7. Accessed By / Used By:**

* **`InputProcessor`:** Identifies existing users by querying `UserExternalIdentity` (to get `user_id` from an `external_id`) or creates new `User` records along with a new `UserExternalIdentity` upon initial contact.
* **`brain:pre-frontal_cortex`:** Extensively reads user profile data (`first_name`, `time_zone`, `locale`, `preferences`) for personalization and decision-making. Updates `last_active_at`.
* **`brain:long_term_mem`:** Stores and retrieves user-specific `LongTermFact`s and `LongTermSummary`s, using `user_id` as the primary link.
* **`ActionExecutor`:** May query `UserExternalIdentity` via `user_id` to retrieve specific `external_id`s (e.g., a CRM ID) needed for actions that interact with external systems on behalf of the user. Also reads user contact info (`email`, `phone_number`).
* **`OutputManager`:** Reads user preferences (`locale`) for output formatting (e.g., TTS voice, language).
* **External User Management/CRM Systems:** May synchronize with this `User` data model.

---

**8. Assumptions / Constraints:**

* `user_id` is the definitive, stable identifier for a user within the VA system.
* **Data privacy and security are paramount** for all `User` data. Strict access controls and encryption must be applied.
* The system relies on the `UserExternalIdentity` table for managing multiple external identifiers.
* Retention policies for `User` data must align with legal and business requirements.