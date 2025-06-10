# 🤝 Contributing to the Virtual Assistant (VA)

First and foremost, thank you for considering contributing to the Virtual Assistant project! Your interest and effort are highly valued. This document outlines guidelines for contributing to ensure a smooth and collaborative experience for everyone.

By contributing to this project, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🚀 How Can I Contribute?

There are many ways you can contribute to the VA project, regardless of your skill level:

* **🐛 Report Bugs:** If you find something that doesn't work as expected, please let us know.
* **✨ Suggest Enhancements:** Have an idea for a new feature or an improvement? We'd love to hear it!
* **💻 Write Code:** Implement new features, fix bugs, improve performance, or refactor existing code.
* **📄 Improve Documentation:** Clarify existing docs, add examples, or write new guides.
* **🗣️ Provide Feedback:** Share your thoughts on existing features, the architecture, or the development process.

## ✍️ Contributing Code

This section details the process and best practices for contributing code changes to the VA.

### 1. Getting Started

Before you start, ensure you have the following prerequisites installed:

* **Git:** For version control.
* **Docker & Docker Compose:** Essential for running local development environments for most services.
* **Python 3.9+:** For core AI and many backend services.
* **Node.js (LTS):** If you plan to work on JavaScript/TypeScript components (e.g., `OutputManager` web UI, or specific backend services).
* **Go 1.20+:** If you plan to work on specific Go-based services.
* **`pre-commit`:** A tool to manage Git pre-commit hooks (install via `pip install pre-commit`).

#### Cloning the Repository:

```bash
git clone [https://github.com/your-org/your-va-project.git](https://github.com/your-org/your-va-project.git)
cd your-va-project
```
#### Setting Up Your Local Environment:

Our microservices architecture allows for flexibility.

1.  **Core Services (via Docker Compose):**
    * For most development, you can spin up the necessary backend services (databases, message queues) using Docker Compose:
        ```bash
        docker-compose -f docker-compose.dev.yml up -d --build
        ```
    * Refer to `docker-compose.dev.yml` for specific service configurations.
2.  **Python Components:**
    * For Python services you're actively developing (e.g., `brain:language_center`, `brain:pre-frontal_cortex`):
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt # Or install for specific component
        ```
    * You can then run the Python service directly from your environment while other services run in Docker.
3.  **Install `pre-commit` Hooks:** This is crucial! These hooks will run automatically before every commit to ensure code quality.
    ```bash
    pre-commit install
    ```

### 2. Finding Something to Work On

* **Good First Issues:** Check the [Issues](https://github.com/your-org/your-va-project/issues) section on GitHub for issues labeled `good first issue`. These are typically smaller, well-defined tasks perfect for new contributors.
* **Help Wanted Issues:** Look for issues labeled `help wanted` for tasks suitable for more experienced contributors.
* **Propose a Feature/Bug Fix:** If you have an idea, open an [Issue](https://github.com/your-org/your-va-project/issues/new/choose) first to discuss it with the maintainers. This helps ensure alignment with the project roadmap.

### 3. Branching Strategy

We use a feature-branch workflow. Please create a new branch for your work:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-awesome-feature # or bugfix/issue-number-fix
```

# 4. Code Style & Quality (Mandatory)

Maintaining a consistent code style and high quality is vital for our project. We heavily rely on automated tools for this.

## 4.1 Automated Checks with pre-commit

All changes **MUST** pass pre-commit hooks. These hooks will automatically format your code and run linters before you commit.  
If a hook fails, pre-commit will tell you why. Fix the issues, `git add` the changed files, and try committing again.

## 4.2 Language-Specific Guidelines

# Python

- **Formatter & Linter:** We use **Ruff** for both code formatting (Black-compatible) and linting (Flake8-compatible, plus many other checks). Ruff helps us enforce consistent style and identify common issues.
- **Type Checker:** We use **MyPy** for static type checking. This helps ensure code correctness and maintainability, especially for larger codebases.
- **Style Guide:** Adhere to [PEP 8](https://peps.python.org/pep-0008/) and our project's specific Ruff configuration (defined in `pyproject.toml`).

#### Local Commands

Before committing, `pre-commit` will automatically run these checks. However, you can run them manually to see results or fix issues:

```bash
ruff check . # Run linters and checks
ruff format . # Run formatter (will apply fixes)
mypy . # Run static type checker
pytest # Run tests
```

### JavaScript/TypeScript

- **Formatter:** Prettier  
- **Linter:** ESLint

#### Local Commands

```bash
prettier --write .
eslint .
```

### Go

- **Formatter:** gofmt (built-in)  
- **Linter:** golint, go vet

#### Local Commands

```bash
go fmt ./...
go vet ./...
golint ./...
```

### Editor Configuration

Please ensure your IDE/editor respects the `.editorconfig` file in the repository root for basic formatting rules (e.g., indentation, line endings).

## 4.3 Polyglot Development & Component Boundaries

Our architecture supports different languages for different microservices. While the MVP leans Python-first, contributions in other languages (e.g., Node.js for a new `InputProcessor` adapter, Go for a high-performance `ActionExecutor` module) are welcome where appropriate.

> **Key Rule:** Regardless of language, your component **MUST** adhere to its defined API contracts (REST endpoints, message queue schemas) with other services.  
> Changes to these contracts require prior discussion and agreement.

---

# 5. Testing

- **Write Tests:** All new features and bug fixes **MUST** include relevant unit tests. For significant changes, integration or E2E tests may also be required.
- **NLU/NLG Testing:** If contributing to `brain:language_center`, ensure you add new test utterances or responses to the evaluation datasets as appropriate.
- **Run Tests Locally:** Before pushing your branch, ensure all tests pass.

### Python

```bash
pytest
```

### Global (via Docker Compose)

```bash
docker-compose -f docker-compose.dev.yml run --rm tests
```

*(or similar service defined in compose)*

---

# 6. Documentation

- **Code Comments:** Write clear, concise comments for complex logic, functions, and classes.
- **API Documentation:** If you modify or add new API endpoints, update the relevant OpenAPI/Swagger specifications.
- **User Documentation:** If your changes impact user-facing behavior, update any relevant documentation in the `docs/` folder.

---

# 7. Commit Messages

We encourage using [Conventional Commits](https://www.conventionalcommits.org/) for clear and consistent commit history. Examples:

- `feat: add new user registration endpoint`
- `fix: resolve issue with entity extraction`

---

# 8. Pull Request (PR) Guidelines

When you're ready to submit your code:

- **Open a Pull Request:** Create a PR from your feature branch to the `main` branch on GitHub.
- **Use the PR Template:** Fill out the provided PR template comprehensively. This helps reviewers understand your changes quickly.
- **Reference Issues:** Link your PR to any relevant issues (e.g., `Fixes #123`, `Closes #456`).
- **Pass CI Checks:** Ensure all automated checks (linting, tests) in the CI pipeline pass successfully.  
  Your PR cannot be merged until they do.
- **Address Review Comments:** Respond to all review comments promptly and professionally. Engage in constructive discussions.
- **Squash Commits (Optional but Recommended):** For clean history, you might be asked to squash your commits into a single logical commit before merging.

---

## 🚨 Reporting Issues

If you find a bug or have a feature request:

- **Check Existing Issues:** Before opening a new issue, search to see if it’s already been reported.
- **Open a New Issue:** If not found, open a new issue and use the provided templates (Bug Report or Feature Request) to give us all the necessary information.  
  Be as detailed as possible.

---

## ❓ Need Help?

If you have questions or need assistance, don't hesitate to:

- Open a [GitHub Discussion](https://github.com/your-repo/discussions)
- Reach out to maintainers via GitHub Issues

---

**Thank you for your valuable contribution!**