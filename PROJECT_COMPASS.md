# V.I.K.I. Project Compass: Path to Operational State

This roadmap focuses on connecting your existing robust components to achieve an end-to-end conversational flow, then layering on intelligence and robustness.

---

## Phase 1: Establish the Core Conversational Loop (Viki "Talking")

**Goal:** Get a user's input to flow through NLU, dialogue management, NLG, and output delivery, with basic logging, to produce a response.

### Tasks:

- [ ] **1. Centralize Custom Errors**
  - [ ] Move `DeviceNotFoundError`, `UnsupportedOutputError`, `TTSConversionError`, `DeliveryChannelError` from `services/output_manager/src/output_manager.py` to `shared_libs/errors/errors.py`.
  - [ ] Update import statements in `services/output_manager/src/output_manager.py` to `from shared_libs.errors.errors import ...`.

- [ ] **2. Refine `PrefrontalCortex` and `LanguageCenter` Integration**
  - [ ] **Modify `services/brain/pre_forntal_cortex/src/pre_frontal_cortex.py`**:
    - [ ] In `__init__`, add `language_center: LanguageCenter` as a parameter and assign it (e.g., `self.language_center = language_center`).
    - [ ] Update `process_dialogue_turn` to:
      - [ ] Construct a **dialogue act** (a structured dictionary) based on NLU results and current dialogue state.
      - [ ] Call `va_response_text = self.language_center.generate_response(dialogue_act_data, conversation_id, user_id)`.
      - [ ] Remove any hardcoded `va_response_text` assignments.
  - [ ] **Modify `main.py`**:
    - [ ] When initializing `PrefrontalCortex`, pass the `language_center` instance.

- [ ] **3. Fully Integrate `ConversationLog`**
  - [ ] **Modify `main.py` Initialization**:
    - [ ] Uncomment and instantiate `ConversationLog` from `services/brain/conversation_log/src/conversation_log.py`.
    - [ ] Ensure `pymongo` is in your `requirements.txt`.
  - [ ] **Modify `data_models/ConversationTurn.md` (and Python class)**:
    - [ ] Ensure `ConversationTurn` (and its Python class in `services/brain/conversation_log/src/conversation_log_interface.py`) has fields for:
      - `nlu_result` (dict)
      - `va_response_text` (str)
      - `action_taken` (str/dict, optional)
      - `dialogue_state_before` (str)
      - `dialogue_state_after` (str)
  - [ ] **Modify `main.py` Interaction Loop**:
    - [ ] Import `datetime` and `UTC` at the top of `main.py`.
    - [ ] After `PrefrontalCortex` processes the turn and you have `va_response_text_final`, create and log two `ConversationTurn` objects:
      - [ ] One for the **user's input**, including `speaker="user"`, `text=user_input`, `nlu_result`, and `dialogue_state_before`.
      - [ ] One for **Viki's response**, including `speaker="viki"`, `text=va_response_text_final`, `action_taken`, and `dialogue_state_after`.
      - [ ] Ensure both turns use the **same `turn_id`** for logical linking.

- [ ] **4. Dynamic `last_active_timestamp` in `ShortTermMemory` Context**
  - [ ] **Modify `services/brain/pre_forntal_cortex/src/pre_frontal_cortex.py`**:
    - [ ] Import `datetime` and `UTC` at the top of the file.
    - [ ] In `process_dialogue_turn`, ensure `current_context["last_active_timestamp"]` is updated with `datetime.now(UTC).isoformat()`.

---

## Phase 2: Expand Intelligence & Persistence (Viki "Remembers" and "Acts")

**Goal:** Viki's responses are influenced by past interactions and long-term knowledge, and it can simulate external actions.

### Tasks:

- [ ] **1. Expand `PrefrontalCortex` Dialogue Policy**
  - [ ] **Modify `services/brain/pre_forntal_cortex/src/pre_frontal_cortex.py`**:
    - [ ] Add more `if/elif` blocks in `process_dialogue_turn` to handle various `intent_name`s (e.g., `greet`, `ask_weather`, `set_reminder`, `tell_joke`, `inquire_personal_info`).
    - [ ] For each intent, define:
      - [ ] How `conversation_context` should be updated in `ShortTermMemory`.
      - [ ] The specific `dialogue_act` (template and parameters) to send to `LanguageCenter` for NLG.
      - [ ] If an external action is needed (see next point).

- [ ] **2. Implement Basic `ActionExecutor` (Mocked)**
  - [ ] **Modify `services/action_executor/src/action_executor.py`**:
    - [ ] Add methods for simulated actions (e.g., `execute_get_time(location: str)`, `execute_set_reminder(item: str, time: str)`, `execute_tell_joke()`). These methods should initially return dummy data or print statements.
  - [ ] **Modify `services/brain/pre_forntal_cortex/src/pre_frontal_cortex.py`**:
    - [ ] When an intent requiring an action is detected, call `self.action_executor.execute_XYZ(...)` with relevant entities from NLU results.
    - [ ] Use the output of this action to inform the `dialogue_act` sent to `LanguageCenter`.

- [ ] **3. Integrate `LongTermMemory` into `PrefrontalCortex`**
  - [ ] **Modify `services/brain/pre_forntal_cortex/src/pre_frontal_cortex.py`**:
    - [ ] **For Retrieval**: Implement logic to call `self.long_term_memory.retrieve_facts(user_id, query_criteria)` based on user questions (e.g., "What's my name?"). Use retrieved facts to enrich the `dialogue_act`.
    - [ ] **For Storage**: Implement logic to call `self.long_term_memory.store_fact(user_id, fact_data)` when Viki learns new, important, or personal information (e.g., "My name is Alex", "I like blue").
  - [ ] **Modify `data_models/LongTermFact.md` (and Python class)**:
    - [ ] Ensure `LongTermFact` (and its Python class in `services/brain/long_term_mem/src/long_term_memory_interface.py`) is structured to hold relevant fact data (e.g., `fact_type`, `value`, `source_conversation_id`, `timestamp`).

---

## Phase 3: Enhance Robustness & Expand Capabilities

**Goal:** Make the system more production-ready, efficient, and capable of new modalities.

### Tasks:

- [ ] **1. Implement `ShortTermMemory` Context Expiration**
  - [ ] **Modify `services/brain/short_term_mem/src/short_term_memory.py`**:
    - [ ] Implement the `TODO` for context expiration. This could be a `cleanup_old_contexts()` method that deletes contexts based on `last_active_timestamp` and a defined Time To Live (TTL).
  - [ ] **Modify `main.py` (or a future orchestrator)**:
    - [ ] Call `short_term_memory.cleanup_old_contexts()` periodically (e.g., every N turns or via a background process).

- [ ] **2. Expand `OutputManager` for Richer Output**
  - [ ] **Modify `services/output_manager/src/output_manager.py`**:
    - [ ] **TTS Integration**: Add logic to support Text-to-Speech (TTS). This would involve a new dependency (e.g., a `TTSService` class wrapping a TTS API). Call this service if `output_format_hints` and `device_capabilities` indicate audio output.
    - [ ] **Rich Media Hints**: Enhance how `output_format_hints` are used to render more than just plain text (e.g., basic Markdown, simple structured cards).

- [ ] **3. Implement Comprehensive Testing**
  - [ ] **Across `services` directories**:
    - [ ] Add **unit tests** for all new logic (especially in `PrefrontalCortex`'s dialogue policy).
    - [ ] Create **integration tests** to verify the flow between components (e.g., `InputProcessor` -> `LanguageCenter` -> `PFC` -> `OutputManager`).
    - [ ] Utilize your existing `tests` directories and `pytest.ini`.

- [ ] **4. Enhance Data Models and Validation**
  - [ ] **Across `data_models` and `services`**:
    - [ ] Keep your Markdown `.md` files in `data_models` updated with any new fields or structures.
    - [ ] Ensure corresponding Python classes (e.g., `ConversationTurn`, `LongTermFact`) in their respective `interface.py` or `src` files accurately reflect these models.
    - [ ] Consider using `Pydantic` for robust data validation and easier serialization/deserialization of your data models.