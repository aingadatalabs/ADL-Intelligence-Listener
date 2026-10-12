# ADL Intelligence Listener

**The source-monitoring and buying-signal collection platform for Ainga Data Labs.**

ADL Intelligence Listener is a modular, asynchronous collection service designed to monitor relevant public sources, normalize source observations, and support the discovery of potential customers for ADL's data engineering, backend engineering, automation, and intelligence products.

The service currently exposes a FastAPI control plane, dispatches asynchronous jobs through Celery, uses Redis for task messaging, and integrates Reddit collection through an internal Reddrix adapter.

Its long-term goal is to provide a common ingestion and signal-processing foundation for Reddit and additional source adapters without coupling the core engine to any single platform.

> **Project status:** Initial Reddit collection architecture. Reddrix is the first source integration. Signal classification, cross-source intelligence, and additional adapters are staged capabilities and should not be considered implemented until their code and tests are available.

---

## Table of Contents

- [1. Purpose and Scope](#1-purpose-and-scope)
- [2. Relationship to ADL SignalForge](#2-relationship-to-adl-signalforge)
- [3. Architecture](#3-architecture)
- [4. Repository Structure](#4-repository-structure)
- [5. Current Capabilities](#5-current-capabilities)
- [6. Requirements](#6-requirements)
- [7. Quick Start](#7-quick-start)
- [8. Configuration](#8-configuration)
- [9. API Reference](#9-api-reference)
- [10. Asynchronous Task Lifecycle](#10-asynchronous-task-lifecycle)
- [11. Adapter and Core Contracts](#11-adapter-and-core-contracts)
- [12. Security and Network Boundaries](#12-security-and-network-boundaries)
- [13. Reliability and Observability](#13-reliability-and-observability)
- [14. Testing and Quality](#14-testing-and-quality)
- [15. Development Workflow](#15-development-workflow)
- [16. Roadmap](#16-roadmap)
- [17. Contributing](#17-contributing)
- [18. License](#18-license)

---

## 1. Purpose and Scope

ADL Intelligence Listener collects relevant source observations that may indicate a potential business need.

Initial use cases include discovering publicly expressed demand for:

- Data engineering, ETL, ELT, and data pipeline development.
- Backend APIs, integrations, and internal automation.
- Web data collection, competitive intelligence, and market monitoring.
- E-commerce pricing, product intelligence, and inventory analytics.
- Data quality, scraping reliability, and infrastructure improvements.
- Technical implementation support for founders and growing businesses.

The system is designed around a simple principle:

**Collect evidence first. Interpret the evidence second. Prioritize opportunities third.**

A post mentioning Python, for example, is not automatically a buying signal. A post describing a broken production pipeline and requesting help fixing it is potentially much more relevant.

The intended processing lifecycle is:

1. Discover source content.
2. Extract source-specific fields.
3. Normalize observations into shared schemas.
4. Deduplicate and validate records.
5. Identify and classify potential buying signals.
6. Match signals to ADL's ideal customer profiles (ICPs) and services.
7. Preserve supporting evidence and source references.
8. Rank opportunities for downstream review and outreach.

The initial implementation focuses on asynchronous source collection and its supporting control plane. The complete intelligence lifecycle will be delivered incrementally.

### Scope boundaries

The Listener is responsible for collection, normalization, and signal-oriented processing.

It is not intended to become:

- A replacement for ADL SignalForge's lead enrichment and outreach workflows.
- A platform-specific scraper embedded directly into the API.
- An unrestricted crawler or arbitrary URL-fetching service.
- An autonomous outreach system that contacts prospects without appropriate controls.

---

## 2. Relationship to ADL SignalForge

ADL operates two complementary systems with different responsibilities.

| System | Primary responsibility | Intended output |
|---|---|---|
| ADL Intelligence Listener | Monitor sources and detect buying signals | Structured observations and signal candidates |
| ADL SignalForge | Discover, enrich, qualify, and prepare leads for outreach | Qualified prospect records and outreach-ready intelligence |

The Listener answers:

**Who is expressing a relevant problem, what evidence supports that interpretation, and when did it occur?**

SignalForge answers:

**Who is the prospect, how does the prospect fit our ICP, how can we contact them appropriately, and what outreach should we prepare?**

The systems should communicate through documented schemas and stable interfaces rather than share tightly coupled scraping implementations.

This separation allows ADL to add new sources, develop additional ICP pipelines, and evolve its go-to-market process independently.

---

## 3. Architecture

The initial runtime consists of three principal infrastructure components:

- **FastAPI:** HTTP control plane for health checks, scrape requests, validation, and task-status queries.
- **Celery worker:** Executes asynchronous collection tasks outside the API request lifecycle.
- **Redis:** Provides the Celery message broker and, where configured, task-result storage.

The application is organized into shared core logic and source-specific adapters.

### Component responsibilities

| Component | Responsibility |
|---|---|
| `apps/listener-api` | Request validation, job submission, health endpoints, and task-status access |
| `packages/core-engine` | Shared data contracts, normalization rules, deduplication interfaces, and proxy policy |
| `packages/adapters/reddit_reddrix` | Reddit-specific collection through the internal Reddrix integration |
| `packages/adapters/linkedin_scraper` | Reserved for a future source adapter |
| `workers/celery_worker` | Celery application, task definitions, execution policy, and routing |
| Redis | Internal task messaging and configured result storage |
| Future persistence layer | Durable storage for normalized observations, signal candidates, and processing metadata |

### Design constraints

- The API must not perform long-running collection synchronously.
- Source-specific behavior must not leak into shared business logic.
- Task execution must be independent of the API process lifecycle.
- Shared schemas must remain stable as new adapters are introduced.
- Durable intelligence records must not depend exclusively on ephemeral task results.
- Network access and proxy usage must be governed by explicit policies.

---

## 4. Repository Structure

The intended monorepo layout is:

```text
adl-intelligence-listener/
├── apps/
│   └── listener-api/
│       └── # FastAPI application and HTTP routes
├── packages/
│   ├── core-engine/
│   │   └── # Shared schemas, models, normalization and policies
│   └── adapters/
│       ├── reddit_reddrix/
│       │   └── # Internal Reddrix integration
│       └── linkedin_scraper/
│           └── # Future adapter
├── workers/
│   └── celery_worker/
│       └── # Celery app, tasks and routing
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

This tree describes the target organization. Directory names and files should be reconciled with the actual repository before treating every entry as present.

### Workspace conventions

The root Python project should own the development toolchain and workspace configuration.

Use one explicitly selected dependency manager, such as `uv` or Poetry, and document its exact commands. Avoid mixing workspace-management conventions without a clear reason.

The API, worker, and source adapters should have explicit dependency boundaries. Shared code should be imported through supported package interfaces rather than fragile working-directory assumptions.

---

## 5. Current Capabilities

The documented initial service provides:

- A FastAPI health endpoint at `GET /health`.
- A Reddit scrape-submission endpoint at `POST /v1/scrape/reddit`.
- An asynchronous task-status endpoint at `GET /v1/tasks/{task_id}`.
- Celery-based background task execution.
- Redis-backed task messaging.
- Docker Compose-based local startup.
- HTTPS subreddit URL validation.
- A requested collection limit restricted to 1–500.
- A maximum of 10 proxy URLs per Reddit scrape request.
- Separation between the HTTP control plane and collection workers.

### Known limitations

- The API does not implement client authentication.
- The API must not be exposed directly to untrusted networks.
- URL validation alone cannot prevent DNS rebinding or private-network access through proxy destinations.
- A healthy API process does not prove that Redis, workers, or the upstream source are healthy.
- Task-result availability depends on the configured Celery result backend and its retention policy.
- Successful collection does not, by itself, mean that a record is a qualified lead or buying signal.

Any additional guarantees—such as persistent storage, idempotent execution, automated signal classification, or cross-source deduplication—must be backed by implemented code and tests.

---

## 6. Requirements

Recommended local development prerequisites:

- Docker Engine with Docker Compose support, or Docker Desktop on Windows.
- Git.
- Access to the repository and its dependencies.
- Network access to the approved upstream sources.
- A supported Python version matching the root project configuration when running tools outside Docker.

Docker Compose is the recommended starting point because it keeps the API, Redis, and worker configuration consistent.

---

## 7. Quick Start

### 7.1 Clone the repository

```bash
git clone <repository-url>
cd adl-intelligence-listener
```

Replace `<repository-url>` with the actual repository URL.

### 7.2 Configure the environment

Inspect `.env.example` and create a local `.env` containing the required configuration.

Do not commit `.env` or other files containing credentials, API keys, or proxy authentication details.

If the project does not yet have an environment template, add one before onboarding additional developers.

### 7.3 Start the service

```bash
docker compose up --build
```

To run the services in the background:

```bash
docker compose up --build -d
```

Inspect service status and logs:

```bash
docker compose ps
docker compose logs -f
```

Inspect a specific service using its actual Compose service name:

```bash
docker compose logs -f <service-name>
```

The API is published on `127.0.0.1:8000` in the local development configuration. Redis should remain accessible only to authorized services on the internal Compose network.

### 7.4 Verify API health

```bash
curl -i http://127.0.0.1:8000/health
```

The expected result is a successful HTTP response when the API process is healthy. Consult the implementation for the exact response schema.

### 7.5 Inspect the API schema

If FastAPI's interactive documentation is enabled in the active environment, open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

These endpoints are for local development. Disable or restrict interactive documentation in production if required by the deployment's security policy.

### 7.6 Stop the service

```bash
docker compose down
```

This stops the Compose services. Named volumes are normally retained unless explicitly removed.

**Warning:** `docker compose down -v` removes associated named volumes and may destroy local data. Use it only when intentionally resetting the environment.

---

## 8. Configuration

Runtime configuration should be supplied through environment variables and validated at application startup.

The exact environment variable names must match the application settings implementation. Do not assume the example names below exist until they have been implemented and documented.

| Setting | Purpose | Operational guidance |
|---|---|---|
| `REDIS_URL` | Internal Redis connection | Keep credentials private and restrict network access |
| `CELERY_BROKER_URL` | Celery broker connection | Use the internal service address in Compose |
| `CELERY_RESULT_BACKEND` | Task-result storage, if configured | Set an intentional result-retention policy |
| `LOG_LEVEL` | Application log verbosity | Use structured, appropriately scoped production logging |
| `APP_ENV` | Runtime environment | Distinguish development, test, and production settings |
| `PROXY_URLS` | Approved proxy configuration, if supported | Protect credentials and enforce destination policy |
| `DATABASE_URL` | Durable persistence, when implemented | Use least-privilege credentials and managed migrations |

### Configuration requirements

- Validate required settings during startup.
- Fail clearly when a required secret or connection setting is missing.
- Never log passwords, tokens, complete authenticated proxy URLs, or other secrets.
- Keep development defaults separate from production settings.
- Use explicit connection, read, and task timeouts.
- Document which service owns each configuration value.

Configuration names in this table are recommendations, not a declaration of the current environment-variable contract.

---

## 9. API Reference

The following endpoints describe the initial HTTP interface.

### `GET /health`

Reports API process health.

```bash
curl -i http://127.0.0.1:8000/health
```

A successful response confirms that the API handler is responding. It should not be interpreted as proof of end-to-end collection readiness.

A future readiness endpoint should verify required dependencies separately, using bounded-time checks.

### `POST /v1/scrape/reddit`

Submits a Reddit collection request for asynchronous execution.

**Input constraints:**

- The target must be an HTTPS Reddit subreddit URL.
- The requested collection limit must be between 1 and 500.
- A request may contain at most 10 proxy URLs.
- Request fields and their exact names must follow the implemented Pydantic request schema.

The route should return a task identifier once the request has been accepted for processing. The exact HTTP status code, response body, and error schema must be confirmed against the implementation.

Example request outline:

```http
POST /v1/scrape/reddit
Content-Type: application/json
```

The JSON body must match the current API model. Do not use an assumed field layout in integrations without checking the OpenAPI schema.

### `GET /v1/tasks/{task_id}`

Retrieves the state of a previously submitted asynchronous task.

```bash
curl -i http://127.0.0.1:8000/v1/tasks/<task-id>
```

On successful completion, the endpoint reports the task result when it remains available in the configured result backend.

The implementation should define consistent responses for:

- Unknown task identifiers.
- Pending or queued tasks.
- Running tasks.
- Successfully completed tasks.
- Failed tasks.
- Results that have expired or are no longer available.

Task identifiers must not be treated as authentication credentials. Once authentication is introduced, task access must be authorized for the requesting principal.

### HTTP contract requirements

Before production integrations depend on the API, document and test:

- Request and response schemas.
- Accepted content types and validation errors.
- HTTP status codes.
- Task-state semantics.
- Retryable versus permanent failures.
- Rate limits and maximum request sizes.
- Authentication and authorization requirements.
- Task-result retention and pagination, if applicable.

---

## 10. Asynchronous Task Lifecycle

The collection lifecycle should follow this model:

1. The client submits a scrape request.
2. FastAPI validates the request and enforces request-level policy.
3. The API dispatches a Celery task.
4. Redis transports the task to an eligible worker.
5. The worker executes the Reddit adapter.
6. The adapter extracts source data and returns structured results or a controlled failure.
7. The task reports completion or failure.
8. The task-status endpoint exposes the state and available result.
9. Future processing stages normalize, deduplicate, persist, and evaluate collected observations.

### Reliability requirements

Production workers should have explicit policies for:

- Network timeouts and bounded execution time.
- Retryable upstream failures and exponential backoff.
- Maximum retry counts.
- Rate limits and upstream throttling.
- Duplicate task delivery and idempotent processing.
- Worker termination and recovery.
- Dead-letter or equivalent handling for repeatedly failing jobs.
- Task-result expiration.
- Graceful shutdown and in-flight task behavior.

Celery delivery and retry settings must be chosen deliberately. Retries can cause repeated upstream requests, and task identifiers alone do not guarantee exactly-once execution.

The desired property is **reliable, observable processing with idempotent effects**, not an unsupported promise of exactly-once delivery.

---

## 11. Adapter and Core Contracts

New source integrations should implement a stable adapter contract rather than create a new API and task architecture for each platform.

### Reddit adapter

`packages/adapters/reddit_reddrix` is the integration boundary for the internal Reddrix fork.

It should be responsible for:

- Translating validated collection requests into Reddrix operations.
- Applying Reddit-specific extraction and source constraints.
- Handling source-specific errors and rate limits.
- Mapping extracted content into the shared observation schema.
- Preserving source identifiers and canonical source URLs.
- Returning structured outcomes suitable for retries, logging, and persistence.

The adapter should not own unrelated ICP qualification or email-sending logic.

### Shared core engine

`packages/core-engine` should own reusable contracts and platform-independent policies.

The normalized observation model should evolve to include fields such as:

| Field | Purpose |
|---|---|
| `source` | Source identifier, such as Reddit |
| `source_record_id` | Stable source-specific record identifier |
| `source_url` | Canonical URL for the observation |
| `observed_at` | When the collection system observed the record |
| `published_at` | Original publication time, when available |
| `text` | Extracted content permitted by the collection policy |
| `author_reference` | Source reference where collection and retention are permitted |
| `metadata` | Validated, source-specific supplementary fields |
| `schema_version` | Version of the normalized contract |

These are proposed schema fields, not a claim that they already exist in the repository.

The core should also define deduplication keys, validation rules, provenance requirements, and persistence interfaces. Source adapters should not independently invent incompatible representations for the same concepts.

### Future adapters

The reserved LinkedIn adapter and subsequent integrations should follow the same contract.

Each new source requires its own review of:

- Terms of service and collection permissions.
- Authentication and access requirements.
- Rate limits and permitted data fields.
- Personal-data handling and retention.
- Reliability and change detection.
- Test fixtures and adapter-specific failure scenarios.

The existence of an adapter directory does not mean the integration is operational.

---

## 12. Security and Network Boundaries

Security is a deployment requirement, not a later enhancement.

### API access

The current API does not implement client authentication.

Until authentication and authorization are implemented:

- Bind the API to loopback for local development.
- Do not expose the service directly to the public internet.
- If remote access is necessary, place it behind an authenticated, access-controlled reverse proxy.
- Restrict network access to approved clients.
- Do not assume that possession of a task identifier grants legitimate access.

An authenticated proxy is a deployment boundary, not a substitute for defining authorization and identity across the complete system.

### Redis

Redis must remain on a private service network.

- Do not publish the Redis port to public interfaces.
- Restrict Redis access to the API, worker, and other explicitly authorized services.
- Use authentication and transport protections appropriate to the deployment.
- Never accept arbitrary client-supplied broker addresses.

### SSRF and proxy validation

The Reddit endpoint accepts at most 10 proxy URLs per request. That limit reduces input volume but does not make proxy usage safe.

HTTPS URL validation alone does not prevent:

- DNS rebinding.
- DNS resolution to loopback, private, link-local, or reserved addresses.
- IPv4 and IPv6 address-based bypasses.
- Redirects to disallowed destinations.
- Access to cloud metadata endpoints.
- A trusted proxy being configured to reach an untrusted internal destination.

Production controls should include:

1. Prefer server-managed proxy identifiers or an approved proxy registry over arbitrary client-supplied proxy URLs.
2. Validate URL schemes, hosts, ports, credentials, and resolved IP addresses.
3. Apply network egress restrictions at the worker or container boundary.
4. Deny loopback, private, link-local, reserved, and metadata-service destinations unless explicitly required and approved.
5. Revalidate destinations after DNS changes and redirects.
6. Restrict permitted outbound destinations where practical.
7. Protect proxy credentials in storage, logs, and task results.

Application-level validation and network-level egress controls must work together.

### Secrets and data protection

- Store credentials outside source control.
- Redact secrets from logs and exception messages.
- Apply least-privilege access to stored observations and task results.
- Establish retention and deletion policies.
- Collect only information needed for a defined business purpose.
- Respect source terms, access restrictions, privacy requirements, and applicable law.

Publicly accessible content is not automatically unrestricted for every collection, storage, or reuse purpose.

---

## 13. Reliability and Observability

The Listener needs visibility into both individual tasks and the overall collection system.

### Structured logging

Logs should include useful correlation fields where available:

- `request_id`
- `task_id`
- `source`
- `adapter_version`
- `attempt`
- `duration_ms`
- `records_extracted`
- `error_category`

Do not log raw credentials, authenticated proxy URLs, or unnecessary personal information.

### Operational metrics

Recommended metrics include:

- Tasks submitted, completed, and failed.
- Queue depth and task wait time.
- Task execution duration.
- Retry counts and upstream error rates.
- Records extracted and rejected.
- Duplicate rates.
- Adapter-specific throttling and failure rates.
- Worker availability and resource utilization.

Metrics should use bounded-cardinality labels. Avoid using raw URLs, post IDs, usernames, or other high-cardinality values as metric labels.

### Health checks

Distinguish between:

- **Liveness:** Is the API or worker process running?
- **Readiness:** Can the service safely accept work given its required dependencies?
- **Collection health:** Are workers processing jobs and receiving expected upstream responses?

A healthy API with a stalled queue is not a healthy end-to-end collection service.

---

## 14. Testing and Quality

Tests should protect the shared contracts and failure behavior before additional source adapters are introduced.

### Unit tests

Cover:

- Request validation.
- URL and proxy policy.
- Shared schema validation.
- Source-record normalization.
- Deduplication rules.
- Retry classification.
- Error mapping.

### Integration tests

Cover:

- API submission and task dispatch.
- Celery worker execution.
- Redis connectivity.
- Task-state transitions.
- Result retrieval and expiration behavior.
- Controlled upstream failures.
- Persistence, when implemented.

### Contract tests

Every adapter should prove that its output satisfies the shared schema and preserves required provenance fields.

Use fixtures and mocked upstream responses for deterministic tests. Avoid relying on live Reddit availability for ordinary unit-test runs.

### Security tests

Cover invalid URL schemes, disallowed IP ranges, DNS changes, redirects, malformed proxy credentials, oversized inputs, unauthorized requests once authentication is implemented, and network-egress enforcement.

### Definition of done

A new adapter is not production-ready merely because it can fetch a page.

It should have validated configuration, documented permissions, stable output contracts, bounded retries and timeouts, useful logs, automated tests, and an explicit failure policy.

---

## 15. Development Workflow

Use the commands supported by the actual root workspace configuration. The following Docker commands are the baseline workflow:

```bash
# Start the complete local stack
docker compose up --build

# Inspect running services
docker compose ps

# Follow service logs
docker compose logs -f

# Stop services
docker compose down
```

For Python development, configure the root workspace to provide consistent commands for formatting, linting, type checking, and testing.

For example, if the corresponding tools are installed and configured:

```bash
pytest
ruff check .
ruff format --check .
```

Do not add these commands to CI as mandatory checks until the dependencies, configuration, test layout, and supported working directory are verified.

### Pull request expectations

Every change should:

1. Preserve API and schema compatibility or explicitly version breaking changes.
2. Include relevant tests.
3. Document new settings and operational requirements.
4. Avoid committing secrets or collected production data.
5. Address source-specific compliance and network-access requirements.
6. Update this README when runtime behavior or the API contract changes.

---

## 16. Roadmap

The roadmap separates infrastructure readiness from intelligence capabilities.

### Phase 1 — Stabilize the Reddit collection service

- Verify the Reddrix integration and shared adapter boundary.
- Finalize the request and response schemas.
- Validate Docker Compose startup and worker connectivity.
- Add deterministic unit, integration, and contract tests.
- Harden URL validation and worker egress.
- Establish bounded retries, task timeouts, and structured logs.
- Document exact configuration and operational commands.

### Phase 2 — Establish normalized observation storage

- Define a versioned cross-source observation schema.
- Implement durable persistence and migrations.
- Add source-aware deduplication and provenance tracking.
- Separate task-result retention from business-data retention.
- Make ingestion idempotent where practical.

### Phase 3 — Build buying-signal intelligence

- Define ADL ICPs and service-specific signal taxonomies.
- Identify intent, urgency, relevance, and evidence strength.
- Introduce configurable rules and, where justified, model-assisted classification.
- Preserve the original evidence supporting each signal.
- Deduplicate repeated observations and rank actionable opportunities.
- Evaluate precision and false-positive rates before relying on automated scores.

### Phase 4 — Expand source coverage

- Implement additional adapters, beginning with sources that offer a strong signal-to-cost ratio.
- Review platform permissions and collection constraints before implementation.
- Reuse shared contracts, worker infrastructure, observability, and storage.
- Add source-specific rate limiting, error handling, and test fixtures.

### Phase 5 — Integrate with ADL SignalForge

- Define a versioned interface for qualified signal candidates.
- Match signals to relevant ADL ICPs and service offerings.
- Enrich prospects through the appropriate downstream pipeline.
- Produce evidence-backed, prioritized opportunities for human review.
- Add controlled handoff to personalized outreach workflows.

### Phase 6 — Production operations

- Implement authentication and authorization.
- Establish deployment-specific secrets management.
- Add readiness checks, metrics, alerts, and operational dashboards.
- Define backup, retention, recovery, and incident-response procedures.
- Load-test queue behavior and enforce capacity limits.

Roadmap items become completed only when implemented, tested, and documented.

---

## 17. Contributing

ADL Intelligence Listener is organized around modular collection, shared contracts, and reliable asynchronous processing.

Contributions should favor:

- Small, testable components.
- Explicit interfaces between the API, workers, core engine, and adapters.
- Typed and versioned data contracts.
- Bounded network access and resource consumption.
- Clear failure semantics.
- Observable and reproducible execution.
- Documented source permissions and data-handling requirements.

New adapters should extend the shared architecture instead of duplicating the entire ingestion stack.

---

## 18. License

The repository's license must be confirmed before distribution.

The use of Reddrix as an internal integration does not automatically determine the license of ADL Intelligence Listener. Verify the upstream project's license, preserve applicable notices, and document the repository's own licensing terms before public release.

---

**Maintained by Ainga Data Labs (ADL)**

Building data systems that turn relevant source observations into actionable business intelligence.