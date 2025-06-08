# Deployment: Kubernetes Strategy

This document details the strategy for deploying the Virtual Assistant (VA) system components onto a Kubernetes cluster. It outlines the use of Kubernetes primitives to orchestrate, manage, and scale the VA, primarily targeting cloud-based production environments where high availability, scalability, and operational efficiency are paramount.

---

## 1. Purpose

To define the specific Kubernetes (K8s) patterns and configurations that will be used to deploy, manage, and scale the VA's microservices architecture. This strategy aims to leverage K8s's robust features for automation, resilience, and resource management, aligning with the "Flexible Deployment Environments" principle.

---

## 2. Core Kubernetes Concepts Applied

The VA components will be mapped to Kubernetes primitives as follows:

* **Pods:** The smallest deployable unit in Kubernetes. Each VA component (e.g., `InputProcessor`, `brain:language_center`) will typically run as one or more containers within a Pod.
* **Deployments:** Used to manage stateless application workloads. Most of the VA's components (e.g., `InputProcessor`, `brain:pre-frontal_cortex`, `ActionExecutor`, `OutputManager`, `brain:language_center`) will be managed by Kubernetes Deployments, enabling declarative updates, rollbacks, and self-healing.
* **Services:** Abstract the underlying Pods and provide stable network endpoints for inter-component communication and external access.
    * **ClusterIP Services:** For internal communication between VA components (e.g., `InputProcessor` communicating with `brain:pre-frontal_cortex`).
    * **NodePort/LoadBalancer Services:** For exposing external endpoints (e.g., `InputProcessor`'s API endpoint, `OutputManager`'s callback listeners) to users or external systems.
* **Ingress:** Manages external access to the services in a cluster, providing HTTP/S routing, SSL termination, and host-based virtual hosting. An Ingress controller (e.g., Nginx Ingress Controller, Traefik) will be used for exposing the VA's public API endpoints.
* **ConfigMaps:** Used to store non-sensitive configuration data (e.g., API URLs, logging levels, feature flags) that needs to be injected into Pods.
* **Secrets:** Used to store sensitive configuration data (e.g., API keys, database credentials) securely within Kubernetes. These should be encrypted at rest (e.g., via KMS integration) and mounted as environment variables or files into Pods.
* **Horizontal Pod Autoscaler (HPA):** Automatically scales the number of Pod replicas up or down based on observed CPU utilization, memory usage, or custom metrics (e.g., queue length for `InputProcessor` or `brain:pre-frontal_cortex`).
* **Persistent Volumes (PV) & Persistent Volume Claims (PVC):** For stateful workloads that require durable storage. While most VA components are stateless, certain shared components or managed services (like databases or message queues if self-hosted) would use PV/PVC.

---

## 3. Component-Specific Deployment Considerations in Kubernetes

* **Stateless Components (e.g., `InputProcessor`, `OutputManager`, `brain:language_center`, `brain:pre-frontal_cortex`, `ActionExecutor`):**
    * Deployed as Kubernetes `Deployments`.
    * Designed for rapid horizontal scaling via HPA.
    * Utilize `ConfigMaps` for environment-specific settings.
    * Access secrets via Kubernetes `Secrets`.
    * Communicate via ClusterIP Services or external message queues.
* **`brain:short_term_mem`:**
    * For high performance and distributed nature, it will likely rely on an **external, managed, in-memory data store** (e.g., managed Redis, Memcached service in the cloud) rather than a K8s-native StatefulSet for the cache itself. This offloads operational complexity.
    * The application component interacting with this cache would still be a stateless Deployment.
* **`brain:long_term_mem`:**
    * The processing component (`brain:long_term_mem` responsible for summarization/fact extraction) will be a standard `Deployment` or potentially a `Job`/`CronJob` for batch processing tasks.
    * Its underlying **persistent data store** (for `LongTermFact` and `LongTermSummary`) should be an **external, managed database service** (e.g., PostgreSQL, NoSQL DB as a managed service) to ensure high availability, backups, and operational ease.
* **`brain:conversationLog` (Service):**
    * The service interacting with the log store will be a `Deployment`.
    * The underlying **log data store** should be a highly scalable, write-optimized **external, managed database or logging service** (e.g., Kafka + Elasticsearch/Loki cluster, or a cloud-native logging service) to handle high ingestion rates. Self-hosting such systems in K8s is complex and usually not recommended unless specific control is needed.

---

## 4. Observability Integration

* **Logging:**
    * Pod logs will be collected by a daemonset (e.g., **Fluent Bit**) running on each node, forwarding logs to a **centralized logging solution** (e.g., managed Elasticsearch/Loki, or cloud-native logging service like CloudWatch Logs, Google Cloud Logging).
    * Log `ConfigMaps` will define logging levels.
* **Monitoring:**
    * **Prometheus** will be deployed within the cluster (or integrated with a managed Prometheus service). It will scrape metrics endpoints from all VA component Pods.
    * **Grafana** will be deployed (or integrated with a managed Grafana service) for dashboarding and visualization of metrics.
    * **Alertmanager** will be used for routing alerts from Prometheus.
* **Distributed Tracing:**
    * **OpenTelemetry** SDKs will be integrated into the VA component applications.
    * **Jaeger** (or a managed tracing service) will be deployed within or alongside the cluster to collect and visualize traces, providing end-to-end visibility across microservices.

---

## 5. Security Best Practices in Kubernetes

* **Network Policies:** Implement Kubernetes Network Policies to enforce strict ingress and egress rules between Pods, limiting communication to only authorized pathways.
* **Role-Based Access Control (RBAC):** Define granular RBAC roles for users and service accounts accessing the Kubernetes API and resources.
* **Secrets Management:** Utilize Kubernetes Secrets, ideally integrated with an external Key Management System (KMS) or a dedicated secrets manager like **HashiCorp Vault**, for sensitive data.
* **Pod Security Standards/Admission Controllers:** Enforce security best practices at the Pod level (e.g., disallowing root user, restricting capabilities).
* **Image Scanning:** Integrate vulnerability scanning of Docker images into the CI pipeline (e.g., Trivy, Clair).
* **Service Accounts:** Assign specific Service Accounts to Pods with least-privilege permissions needed to interact with Kubernetes APIs or cloud services.

---

## 6. CI/CD Integration with Kubernetes

Automated CI/CD pipelines will manage the lifecycle of VA components in Kubernetes:
* **Continuous Integration:** On code commit, builds Docker images, runs unit/integration tests, and pushes images to a container registry.
* **Continuous Deployment:**
    * **Declarative GitOps tools** (e.g., **Argo CD**, **Flux CD**) are preferred to automatically synchronize the desired state defined in Git with the running state in the Kubernetes cluster.
    * Alternatively, native cloud services (e.g., AWS CodePipeline, GCP Cloud Build) can orchestrate deployments.
* **Rollbacks:** CI/CD pipelines will support automated rollbacks to previous stable versions in case of deployment failures.

---

This `deployment/kubernetes_deployment.md` provides a detailed plan for deploying your VA system on Kubernetes, outlining the specific tools and practices that align with a robust, scalable, and cost-effective cloud environment.

Next, we can tackle the remaining data models: `data_models/UserExternalIdentity.md`. How does this Kubernetes plan look?