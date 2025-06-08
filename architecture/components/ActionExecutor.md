# Component Specification: `ActionExecutor`

**1. Component Name:** `ActionExecutor`

**2. Conceptual Role / Nickname:** Tool Runner / Task Agent / The "Hands" / The "Doer"

**3. Purpose / Mission:**
The `ActionExecutor` is responsible for receiving structured action requests from the `brain:pre-frontal_cortex` and reliably executing the corresponding external tools, internal scripts, or direct system commands. Its mission is to bridge the gap between the virtual assistant's cognitive processes and its ability to interact with the physical and digital world, performing tasks on behalf of the user.

---

**4. Core Responsibilities:**

* **Action Mapping:** Maintain a registry or mapping of defined `action_name`s to the specific underlying tool, script, or command necessary for their execution.
* **Parameter Validation & Transformation:** Validate that the `action_parameters` provided are correct and transform them into the format required by the target tool/script.
* **Tool/Script Invocation:** Securely invoke the identified tool, script, or external API with the correct parameters. This could involve making HTTP requests, calling libraries, executing shell commands, or running Python functions.
* **Credential Management:** Securely retrieve and apply any necessary authentication credentials (API keys, tokens) for external services or restricted commands, distinguishing between system-level secrets and user-specific credentials.
* **Result Handling:** Capture the output, success/failure status, and any error messages from the executed action.
* **Result Reporting:** Format the execution results into a standardized response and return it to the `brain:pre-frontal_cortex` for dialogue continuation.
* **Error Management:** Gracefully handle various execution failures (e.g., network errors, API rate limits, script exceptions, invalid arguments) and report them clearly.
* **Concurrency Management (Optional):** If multiple actions can be executed concurrently, manage the execution queues and limits.

---

**5. External Interfaces / APIs:**

The `ActionExecutor` typically exposes one primary API for the `pre-frontal_cortex` to request actions:

* `execute_action(action_name, action_parameters, user_id=None, conversation_id=None)`

#### API Definition: `execute_action`

* **Description:** Initiates the execution of a named action with the provided parameters.
* **Parameters:**
    * `action_name` (`str`): The logical name of the action to be performed (e.g., "get_weather", "set_alarm", "turn_on_light", "send_email").
    * `action_parameters` (`dict`): A dictionary of key-value pairs representing the arguments required for the action (e.g., `{'location': 'London'}`, `{'time': '8:00 AM', 'message': 'Wake up!'}`).
    * `user_id` (`UUID`, optional): The ID of the user requesting the action. Crucial for user-specific actions or retrieving user-specific credentials.
    * `conversation_id` (`UUID`, optional): The ID of the current conversation. Useful for logging or context if an action is long-running.
* **Returns:** (`dict`) A dictionary containing the outcome of the action execution:
    ```json
    {
        "success": true,              // Boolean indicating if the action completed without error.
        "result_data": {              // Dictionary of any data returned by the action.
            "message": "string",      // Human-readable message (e.g., "Weather is 20C")
            "raw_output": "any",      // Raw output from the tool/API (e.g., JSON response)
            "status": "string"        // Specific status from the tool (e.g., "booked", "failed_auth")
            // ... any other structured data relevant to the action (e.g., "temperature": 20)
        },
        "error": {                    // (Optional) Dictionary if success is False.
            "code": "string",         // e.g., "API_ERROR", "TIMEOUT", "SCRIPT_FAILED"
            "message": "string",      // Human-readable error description
            "details": "string"       // Optional, technical details (e.g., stack trace snippet)
        }
    }
    ```
* **Possible Errors (Internal to ActionExecutor):**
    * `ActionNotFoundError`: `action_name` is not recognized.
    * `InvalidParametersError`: Required `action_parameters` are missing or malformed.
    * `ExecutionFailedError`: The underlying tool/script reported an error.
    * `AuthorizationError`: Missing or invalid credentials for the action.
    * `ServiceUnavailableError`: External service is down or unreachable.

---

**6. Internal Logic / Algorithm (Detailed Steps for `execute_action`):**

* **Step 1: Action Lookup:**
    * Consult an internal "Action Registry" (e.g., a dictionary or configuration loaded from a dedicated store) to find the handler for `action_name`.
    * IF `action_name` not found: Return `ActionNotFoundError`.
* **Step 2: Parameter Validation & Preparation:**
    * Retrieve the expected parameter schema for the identified action from the registry.
    * Validate `action_parameters` against the schema (e.g., check for required fields, data types).
    * IF validation fails: Return `InvalidParametersError`.
    * Transform `action_parameters` into the exact format required by the underlying tool/script (e.g., converting a temperature unit, formatting a date).
* **Step 3: Credential Retrieval (If Necessary):**
    * IF the action requires authentication (e.g., API key for a weather service, OAuth token for an email client):
        * Determine if it's a **system-level credential** (e.g., the VA's own API key for a general service) or a **user-specific credential** (e.g., a user's personal OAuth token).
        * Retrieve **system-level credentials** from a **Dedicated Secret Management System**.
        * Retrieve **user-specific credentials** using `user_id` from **`brain:long_term_mem`** (which would store them securely, e.g., encrypted).
        * IF credentials invalid/missing: Return `AuthorizationError`.
* **Step 4: Tool/Script Invocation:**
    * This is the core execution step. The specific method depends on the nature of the tool:
        * **External API Call:** Make an HTTP request (GET, POST, etc.) to the service endpoint.
        * **Python Script Execution:** Import and call a specific Python function, or use `subprocess.run()` to execute a separate script file.
        * **Home Automation Command:** Call a specific library function that interfaces with a smart home hub API.
        * **Direct System Command:** Carefully execute a shell command (with extreme caution and sandboxing).
    * Wrap the invocation in `try-except` blocks to catch runtime errors.
* **Step 5: Result Processing:**
    * Capture the raw output from the tool/script (e.g., JSON response, standard output).
    * Parse and normalize the raw output into the `result_data` dictionary.
    * Determine `success` status based on HTTP status codes, error messages, or script return codes.
* **Step 6: Return Formatted Result:**
    * Return the `success` status, `result_data`, and `error` object (if `success` is `False`).

---

**7. Data Interactions:**

* **Reads from:**
    * **Internal Action Registry / Configuration Store:** For action definitions, schemas, and non-secret tool configurations (e.g., loaded from dedicated configuration files or a config service).
    * **Dedicated Secret Management System:** For system-level API keys and other sensitive credentials required by the VA itself to interact with external services.
    * **`brain:long_term_mem`**: For *user-specific* external service tokens/credentials (e.g., a user's OAuth token for their smart home device).
* **Writes to:**
    * **External Systems/APIs**: This is the primary output – it changes the state of the world (e.g., sets an alarm, turns on a light, sends an email).
    * **Logging System**: For auditing and debugging tool executions.

---

**8. Dependencies:**

* **HTTP Client Library:** (e.g., `requests` in Python) for web API interactions.
* **Specific SDKs/Libraries:** For interacting with home automation systems, email services, etc.
* **Subprocess Module:** (If executing external scripts/commands).
* **Dedicated Secret Management System Client:** For secure access to system-level secrets.
* **`brain:long_term_mem`**: For retrieving user-specific credentials.
* **Configuration Management System/Loader:** For loading action registry and non-secret configurations.
* **Logging Framework:** For auditing and debugging.

---

**9. Assumptions / Constraints:**

* All tools/actions that the VA can perform are pre-configured and accessible by the `ActionExecutor`.
* **Security is paramount:** Input validation, secure credential handling (using dedicated secret management where appropriate), and robust sandboxing for script/command execution are critical.
* Error handling for external services is robust to prevent cascading failures.
* Actions are generally atomic; complex, multi-step user requests should be broken down into sequential `action_name` calls by the `brain:pre-frontal_cortex`.
* The `ActionExecutor` primarily focuses on *execution*, not on *deciding* which action to take or *interpreting* complex outputs for dialogue; that's the `pre-frontal_cortex`'s role.