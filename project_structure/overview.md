# Project Structure Overview

This document describes the high-level directory and file structure of the Virtual Assistant (VA) project repository. A well-organized structure is crucial for readability, maintainability, and for guiding new contributors.

---

## 1. Top-Level Directories and Files

The root of the repository contains essential project-level files and directories.

* **`.github/`**:
    * Contains GitHub-specific configurations.
    * **`workflows/`**: GitHub Actions CI/CD workflows (e.g., `ci.yml`, `deploy.yml`).
    * **`ISSUE_TEMPLATE/`**: Templates for bug reports and feature requests.
    * **`PULL_REQUEST_TEMPLATE.md`**: Template for guiding Pull Request descriptions.
* **`architecture/`**:
    * Core architectural documentation that defines the VA's design principles, components, and interactions.
    * `overview.md` (System overview, component map)
    * `principles.md` (Design philosophy)
    * `contribution_guidelines.md` (Optional: if detailed architectural contribution guidelines are separate from general code)
* **`data_models/`**:
    * Definitions of the core data models used across the system.
    * `ConversationContext.md`
    * `LongTermFact.md`
    * `LongTermSummary.md`
    * `UserExternalIdentity.md`
    * *(Potentially: `Device.md`, `User.md`, `Conversation.md` if defined separately)*
* **`deployment/`**:
    * Configuration files and scripts related to deploying the VA system.
    * `overview.md` (Deployment strategy)
    * `kubernetes_deployment.md` (Kubernetes manifests, Helm charts)
    * `docker-compose.yml` (Primary development and local deployment compose file)
    * `docker-compose.dev.yml` (Development-specific overrides for Docker Compose)
    * `prod/` (Production-specific configuration, e.g., Kubernetes manifests, terraform files)
* **`docs/`**:
    * General user-facing documentation, installation guides, how-tos, and FAQs.
    * `installation.md`
    * `usage_guide.md`
    * `faq.md`
    * `api_reference.md` (If API docs are static Markdown)
* **`front_end/`**:
    * Code and documentation specific to the user interfaces/channels.
    * `overview.md` (Front-end strategy)
    * `web_widget/` (Code for an embeddable web chat widget, e.g., React/Vue project)
    * `mobile_app/` (Code for a mobile app, e.g., React Native/Flutter project)
    * `messaging_adapters/` (If channel-specific logic for messaging platforms resides here, though often handled by `InputProcessor`/`OutputManager` components)
* **`services/`**:
    * This is the core directory for the VA's microservices. Each service will reside in its own subdirectory.
    * **`action_executor/`**: Contains the code for the Action Executor service.
    * **`brain/`**: Contains the core "brain" services.
        * `language_center/`
        * `pre_frontal_cortex/`
        * `long_term_mem/`
        * `short_term_mem/`
        * `conversation_log/`
    * **`input_processor/`**: Code for handling incoming user input from various channels.
    * **`output_manager/`**: Code for sending responses back to users via various channels.
    * *(Add other services as they are defined, e.g., `user_management/`, `device_manager/`)*

    * **Inside each `services/<service_name>/` directory:**
        * `src/`: Main source code files (e.g., `.py`, `.js`, `.go`).
        * `tests/`: Unit and component tests for this specific service.
        * `Dockerfile`: Containerization definition for the service.
        * `requirements.txt` / `package.json` / `go.mod` / `pom.xml`: Language-specific dependency files.
        * `config.py` / `config.json`: Service-specific configuration.
        * `README.md`: Specific overview for this service.
* **`shared_libs/`** (or `common/`):
    * Reusable code, libraries, or definitions shared across multiple services to avoid duplication.
    * `schemas/` (e.g., Protobuf, Avro, or JSON schemas for message queues)
    * `utils/` (Common utility functions, decorators)
* **`tools/`** (or `scripts/`):
    * Miscellaneous development or operational scripts.
    * `setup.sh` (Initial setup script)
    * `build.sh` (Build automation script)
    * `run_tests.sh` (Wrapper for running all tests)
    * `data_importer/` (Scripts for importing initial data)
* **`models/`**:
    * If large AI models or datasets are versioned with the repository (though often managed externally for size).
    * `nlu_models/`
    * `embedding_models/`
    * `training_data/`
    * `evaluation_scripts/`

## 2. Root-Level Files

* **`README.md`**: The primary project README (as described above).
* **`CONTRIBUTING.md`**: Guidelines for contributors (as discussed).
* **`CODE_OF_CONDUCT.md`**: Defines behavioral expectations for the community.
* **`LICENSE`**: Specifies the open-source license under which the project is released.
* **`.gitignore`**: Specifies intentionally untracked files to ignore.
* **`.editorconfig`**: Defines coding style and configuration for various editors.
* **`requirements.txt` / `pyproject.toml`**: (If any global Python dependencies for tools/scripts).

---

This structure provides a clear, scalable, and intuitive layout for your Virtual Assistant project on GitHub, making it easier for both maintainers and new contributors to navigate and understand the system.