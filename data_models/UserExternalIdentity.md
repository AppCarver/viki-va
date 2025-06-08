# Data Model: `UserExternalIdentity`

**1. Data Model Name:** `UserExternalIdentity`

**2. Conceptual Role / Nickname:** External User ID Mapping / Identity Linker / External Account Linker

**3. Purpose / Mission:**
The `UserExternalIdentity` data model is designed to securely store and manage the mappings between a virtual assistant's internal `user_id` and various external system user identifiers. Its mission is to enable the VA to recognize and interact with a single user across multiple external platforms (e.g., CRM, messaging apps, SSO providers), ensuring consistent user experience and data integration.

---

**4. Schema Definition:**

This model defines the core attributes and structure for linking a `User` to a specific external identity.

* **`external_identity_id`** (`UUID`, Primary Key)
    * **Description:** A unique identifier for this specific external identity mapping.
    * **Example:** `1a2b3c4d-5e6f-7890-abcd-ef0123456789`
* **`user_id`** (`UUID`, Foreign Key to `User` model, Indexed)
    * **Description:** The unique identifier of the internal `User` record to which this external identity belongs.
    * **Example:** `7890abcdef-1234-5678-90ab-cdef12345678`
* **`system_name`** (`String`, Indexed)
    * **Description:** A standardized name identifying the external system or platform this `external_id` originates from. This should be a controlled vocabulary (e.g., "CRM", "SLACK", "SSO", "ALEXA", "TWILIO", "DISCORD").
    * **Example:** `"SLACK"`
* **`external_id`** (`String`, Indexed)
    * **Description:** The actual unique identifier for the user within the `system_name` external system.
    * **Example:** `"U123456789"` (Slack user ID), `"CUST98765"` (CRM ID)
* **`created_at`** (`DateTime`, Indexed)
    * **Description:** The timestamp when this external identity mapping was first created.
    * **Example:** `2025-06-06T17:40:00Z`
* **`updated_at`** (`DateTime`, Indexed)
    * **Description:** The timestamp of the last update to this external identity mapping.
    * **Example:** `2025-06-06T17:40:00Z`

---

**5. Relationships:**

* **Many-to-One (`UserExternalIdentity` to `User`):**
    * Multiple `UserExternalIdentity` records can be linked to a single `User` record (a user can have many external identities). The `user_id` serves as the foreign key.
* **Unique Constraint:**
    * A unique constraint should be enforced on the combination of `(system_name, external_id)`. This ensures that a specific external ID from a specific system can only map to one internal `user_id` at a time.

---

**6. Lifecycle Considerations:**

* **Creation:**
    * Typically created by the **`InputProcessor`** when a user interacts for the first time via a *new* `Device` or platform that provides an identifiable `external_id` (and this `external_id` is not yet linked to an existing internal `User`).
    * Can also be created by explicit user actions (e.g., linking accounts through a VA command) or by administrative tools.
* **Updates:** Updates are rare for this model, primarily `updated_at` timestamps or if an external system's ID for a user somehow changes (which is uncommon).
* **Deletion:**
    * When a user account (`User` record) is deleted, all associated `UserExternalIdentity` records must also be deleted.
    * If a user unlinks an external account, the specific `UserExternalIdentity` record can be deleted.

---

**7. Accessed By / Used By:**

* **`InputProcessor`:** This is a primary consumer. It receives an `external_id` from an incoming `Device` message and queries `UserExternalIdentity` to find the associated `user_id`. If not found, it might trigger the creation of a new `User` and `UserExternalIdentity`.
* **`brain:pre-frontal_cortex`:** May query to retrieve specific `external_id`s for a `user_id` if it needs to interact with an external system on behalf of that user (e.g., "Send a Slack message to Alice").
* **`ActionExecutor`:** When executing an action that requires an `external_id` for a specific system (e.g., sending a message via a Slack API for a user), it would query this table via `user_id` to get the necessary `external_id`.
* **User Management / Integration Services:** Used for linking/unlinking external accounts and managing user identity across systems.

---

**8. Assumptions / Constraints:**

* The combination of `(system_name, external_id)` is globally unique and serves as the primary way to identify a user *from an external system's perspective*.
* `system_name` values are well-defined and consistently used across the system.
* Security: `external_id`s themselves might not be sensitive, but their link to an internal `user_id` is. Access to this mapping table must be carefully controlled.