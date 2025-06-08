# Technology Stack Choices

This document outlines recommended technology choices for key components of the Virtual Assistant (VA) system, specifically focusing on databases, message queues, and AI models. These selections prioritize flexibility, scalability, and adherence to the principle of cost-effectiveness, while also allowing for the integration of advanced commercial AI capabilities.

---

## 1. Databases

For persistent data storage, a mix of relational and NoSQL databases can be utilized based on the specific data access patterns and scalability needs of each component.

### 1.1 Relational Database (for structured data and transactional integrity)

* **Primary Use Cases:** `User`, `Device`, `Conversation` (metadata), `UserExternalIdentity`, `LongTermFact` (if highly structured), `ConversationLogService` (if strong ordering/audit trail is paramount and throughput can be managed).
* **Recommended Open-Source Technology:** **PostgreSQL**
    * **Why:** Robust, highly extensible, feature-rich, strong community support, excellent ACID compliance, and well-suited for complex queries. It's often considered the "Swiss Army knife" of databases.
    * **Deployment Options:**
        * **Self-hosted:** Can be deployed on a VM, or via Kubernetes `StatefulSet` (more complex to manage yourself for high availability).
        * **Managed Service (Cloud Option):** Available as managed services on all major cloud providers (e.g., AWS RDS for PostgreSQL, Google Cloud SQL for PostgreSQL, Azure Database for PostgreSQL). While incurring cost, these significantly reduce operational overhead for production environments.

### 1.2 NoSQL Database / Key-Value Store (for high throughput, flexible schemas, and caching)

* **Primary Use Cases:** `ConversationContext` (as a cache/session store for `brain:short_term_mem`), `ConversationLogService` (for very high write throughput where strict ordering isn't always needed, e.g., raw logs), potentially `LongTermFact` (if schema is highly dynamic).
* **Recommended Open-Source Technologies:**
    * **Redis (Key-Value Store/Cache):**
        * **Why:** Extremely fast in-memory data structure store, ideal for caching, session management, and `ConversationContext`. Supports various data structures (strings, hashes, lists, sets, sorted sets).
        * **Deployment Options:** Self-hosted or managed cloud services (e.g., AWS ElastiCache for Redis, Azure Cache for Redis).
    * **Apache Cassandra (Column-Family Store):**
        * **Why:** Designed for high availability, massive scalability, and high write throughput across multiple data centers. Excellent for `ConversationLogService` if extreme scale is anticipated and eventual consistency is acceptable.
        * **Deployment Options:** Self-hosted distributed cluster (complex to manage), or cloud-managed options (e.g., Datastax Astra DB, AWS Keyspaces).
    * **MongoDB (Document Database):**
        * **Why:** Flexible schema allows easy storage of complex JSON-like documents, well-suited for data where schema might evolve. Good for initial rapid development or semi-structured `LongTermFact` storage.
        * **Deployment Options:** Self-hosted or MongoDB Atlas (managed service).

---

## 2. Message Queues

Message queues are essential for asynchronous communication, decoupling components, buffering workloads, and enabling event-driven architectures.

* **Primary Use Cases:**
    * **`InputProcessor` to `brain:pre-frontal_cortex`:** Buffering incoming user messages.
    * **`brain:pre-frontal_cortex` to `ActionExecutor`:** Asynchronous action requests.
    * **`brain:long_term_mem` for background processing:** Event streaming for summarization/fact extraction.
    * **Cross-service communication:** General eventing and inter-service messaging.
* **Recommended Open-Source Technologies:**
    * **Apache Kafka:**
        * **Why:** A distributed streaming platform highly optimized for high-throughput, fault-tolerant message queues and real-time data feeds. Ideal for event sourcing, logging streams (`brain:conversationLog`), and inter-service communication at scale.
        * **Deployment Options:** Self-hosted cluster (requires expertise), or managed cloud services (e.g., Confluent Cloud, AWS MSK, Azure Event Hubs).
    * **RabbitMQ:**
        * **Why:** A general-purpose, robust message broker supporting various messaging patterns (publish/subscribe, work queues, routing). Easier to set up and manage than Kafka for smaller-to-medium scale needs.
        * **Deployment Options:** Self-hosted, or managed cloud services.
    * **Redis (Pub/Sub):**
        * **Why:** While not a full-fledged message queue, Redis's Pub/Sub capabilities can be used for simple, fire-and-forget message broadcasting or intra-application events where durability isn't critical.

---

## 3. AI Models and Frameworks

These technologies power the VA's intelligence, primarily within the `brain:language_center` and `brain:long_term_mem`. The strategy involves a **hybrid approach**, leveraging both robust open-source models and powerful commercial APIs.

### 3.1 Core Natural Language Understanding (NLU - Intent Recognition, Entity Extraction)

* **Recommended Open-Source Frameworks/Libraries:**
    * **Hugging Face Transformers:** Provides access to thousands of pre-trained models (e.g., BERT, RoBERTa, DistilBERT, XLM-RoBERTa) for various NLP tasks. Excellent for fine-tuning on custom datasets for intent classification and named entity recognition.
    * **spaCy:** A highly optimized and production-ready NLP library for Python, strong for linguistic annotations, rule-based entity matching, and custom statistical models. Often complements Transformer models.
    * **Rasa NLU (part of Rasa Open Source):** If a more complete conversational AI framework is desired for NLU and dialogue management, Rasa offers integrated components.
* **Models:** Custom fine-tuned versions of open-source models like BERT, RoBERTa, DistilBERT on your specific domain data.

### 3.2 Natural Language Generation (NLG - Response Generation) & Advanced AI Reasoning

* **Recommended Approaches/Technologies:**
    * **Templating Engines (for rule-based/templated responses):**
        * **Why:** For predictable or structured responses, using templates with placeholders is efficient and controllable.
        * **Technologies:** Jinja2 (Python), Handlebars (JavaScript), or similar.
    * **Open-source Generative Models:**
        * **Why:** Fine-tuning smaller generative models (e.g., GPT-2, T5, BART variants from Hugging Face) or utilizing emerging open-source LLMs (e.g., Llama variants, Mistral, Gemma) allows for more flexible and natural-sounding responses while maintaining local control and avoiding per-token costs.
    * **Commercial Large Language Model (LLM) APIs (e.g., Google's Gemini-Flash/Pro, OpenAI's GPT models):**
        * **Why:** These APIs offer state-of-the-art performance, advanced reasoning capabilities, broader general knowledge, and often multimodal understanding (text, image, audio, video input/output). They significantly reduce the burden of model hosting and management.
        * **Use Cases for Commercial APIs:**
            * **Complex Queries & Fallback:** Serving as a fallback for `brain:language_center` when open-source models struggle with highly complex, ambiguous, or novel user requests.
            * **Advanced Summarization & Fact Extraction (`brain:long_term_mem`):** Leveraging their superior understanding for generating high-quality summaries from extensive conversation logs or extracting nuanced facts.
            * **Creative Content Generation:** For tasks requiring more creative or flexible text generation beyond templated responses.
            * **Multimodal Interactions:** If the VA needs to process images, audio, or video input from users, these APIs offer robust multimodal capabilities.
        * **Considerations:** Integration requires API keys and incurs usage-based costs. Cost management strategies (rate limiting, token budgeting) should be implemented.

### 3.3 Embeddings

* **Recommended Models:**
    * **Sentence Transformers (Hugging Face):** Provides pre-trained models for generating high-quality sentence embeddings, crucial for semantic search, similarity, and retrieval-augmented generation (RAG).
    * **OpenAI Embeddings API / Gemini Embedding API:** Commercial embedding services offer high-quality embeddings with ease of use, though at a cost.

### 3.4 Model Serving / Deployment

* **Recommended Open-Source Tools:**
    * **FastAPI (Python):** A modern, fast (high-performance) web framework for building APIs, excellent for serving ML models via HTTP endpoints.
    * **ONNX Runtime:** A cross-platform inference engine that can accelerate the execution of machine learning models.
    * **BentoML:** An open-source framework for building, shipping, and operating AI applications, providing tools for model serving, packaging, and deployment.
    * **MLflow:** An open-source platform for managing the end-to-end machine learning lifecycle, including tracking experiments, packaging code, and deploying models.

---

## 4. General Application Frameworks (Backend Components)

For building the individual microservices.

* **Recommended Open-Source Choices:**
    * **Python:**
        * **FastAPI:** For high-performance async APIs (e.g., `InputProcessor`, `OutputManager`, `ActionExecutor`, `brain:language_center`'s inference endpoint).
        * **Flask:** For simpler, lightweight APIs.
        * **Celery:** For distributed task queues and asynchronous background processing.
    * **Node.js:**
        * **Express.js:** A minimalist web framework for APIs.
        * **NestJS:** A progressive Node.js framework for building efficient, scalable, and enterprise-grade server-side applications.

---

This revised `technologies/stack_choices.md` now explicitly includes the option and strategic reasoning for incorporating commercial LLM APIs.

Next up, we'll shift gears to **"Start thinking about the user interface/front-end aspects."**