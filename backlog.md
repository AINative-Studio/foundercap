## Epic 1: Project Initialization & Configuration

**Goal:** Establish the foundation—repo, CI/CD, configuration, and scheduling.

* **US-1.1** — *Repository & CI/CD*

  * **As** a developer
  * **I want** a Git repo with linting, testing, and build pipelines
  * **So that** every change is validated automatically
  * **Acceptance Criteria:**

    * CI runs on every PR: lint, unit tests pass.
    * Build artifact (Docker image) produced on merge to main.

* **US-1.2** — *Environment Configuration*

  * **As** an Ops engineer
  * **I want** secure storage of API keys and environment variables
  * **So that** credentials for LinkedIn, Crunchbase, Airtable, ZeroDB are not in code
  * **Acceptance Criteria:**

    * Secrets stored in AWS Secrets Manager (or your vault).
    * App reads credentials at runtime; missing secrets fail startup with clear error.

* **US-1.3** — *Scheduler Setup*

  * **As** a scheduler
  * **I want** a cron/Celery-beat job that triggers the agent at a configurable cadence
  * **So that** scrapes run automatically without manual intervention
  * **Acceptance Criteria:**

    * Scheduler config file with default “every hour.”
    * Successful trigger logs a heartbeat entry in the system log.

---

## Epic 2: Data Ingestion (Scrapers & Alerts)

**Goal:** Build the connectors to LinkedIn, Crunchbase, and Google Alerts.

* **US-2.1** — *Crunchbase API Module*

  * **As** a data engineer
  * **I want** a `fetch_crunchbase(permalink)` function
  * **So that** I can retrieve normalized funding data
  * **Acceptance Criteria:**

    * Returns `{ total_funding, funding_stage, investors[] }`.
    * Handles API errors and rate limits gracefully.

* **US-2.2** — *LinkedIn Scraper Module*

  * **As** a data engineer
  * **I want** to fetch company details (status, website, headcount) via API or Playwright
  * **So that** I can enrich our company profiles
  * **Acceptance Criteria:**

    * Extracts valid fields for a test list of companies.
    * Retries on transient errors; flags hard failures.

* **US-2.3** — *Google Alerts Ingestion*

  * **As** a program manager
  * **I want** to receive Google Alert RSS items via webhook
  * **So that** new news items are queued for processing
  * **Acceptance Criteria:**

    * Zapier or custom endpoint ingests RSS → queue.
    * Deduplication prevents reprocessing the same alert.

* **US-2.4** — *Raw Alert Storage*

  * **As** a system
  * **I want** to store raw alerts in a simple “Alerts” table/queue
  * **So that** downstream processes can normalize and attach to companies
  * **Acceptance Criteria:**

    * Raw alerts persisted with timestamp, title, URL.
    * Alerts marked “unprocessed” by default.

---

## Epic 3: Change Detection & Snapshotting

**Goal:** Compare newly fetched data to prior state and capture snapshots.

* **US-3.1** — *Snapshot Store Interface*

  * **As** a developer
  * **I want** to read/write snapshots in ZeroDB (and cache locally)
  * **So that** I can diff against the last known state
  * **Acceptance Criteria:**

    * Can fetch the most recent snapshot for a given `company_id`.
    * Can write a new snapshot with timestamp and full data.

* **US-3.2** — *Diff Engine*

  * **As** a developer
  * **I want** an algorithm that compares two JSON objs and returns changed fields
  * **So that** I only update what has actually changed
  * **Acceptance Criteria:**

    * Given two sample payloads, diff returns minimal `{ field: [old, new] }`.
    * Zero changes → empty diff.

* **US-3.3** — *Snapshot Persistence*

  * **As** a system
  * **I want** to automatically save a snapshot after each successful run
  * **So that** I maintain a history of company state over time
  * **Acceptance Criteria:**

    * On successful diff & update, new snapshot written.
    * Historical snapshots can be retrieved in chronological order.

---

## Epic 4: Data Store Synchronization

**Goal:** Apply detected changes to Airtable and ZeroDB, and refresh dashboard cache.

* **US-4.1** — *Airtable Updater*

  * **As** a program manager
  * **I want** changed fields patched to Airtable
  * **So that** the base remains the single source of truth
  * **Acceptance Criteria:**

    * Only fields in the diff are sent in the `PATCH` request.
    * Airtable record updated correctly; API errors logged.

* **US-4.2** — *ZeroDB Upsert*

  * **As** a system
  * **I want** to upsert enriched company records via ZeroDB API
  * **So that** I maintain a performant, searchable data store
  * **Acceptance Criteria:**

    * Upsert includes updated fields and new snapshot.
    * New record or existing record updated without error.

* **US-4.3** — *Cache Invalidation*

  * **As** a front-end user
  * **I want** the dashboard to reflect changes immediately
  * **So that** I never see stale data
  * **Acceptance Criteria:**

    * After every upsert, `POST /cache/invalidate` is called.
    * Front-end refresh returns fresh data on the next request.

---

## Epic 5: Dashboard & Analytics Integration

**Goal:** Ensure the front-end displays accurate, query-optimized startup data.

* **US-5.1** — *ZeroDB Query Service*

  * **As** a front-end developer
  * **I want** a read-API layer over ZeroDB for table & filter operations
  * **So that** I can drive the UI with fast queries
  * **Acceptance Criteria:**

    * Supports pagination, sorting, filtering by any field.
    * Returns results in under 200ms (for up to 1,000 records).

* **US-5.2** — *Detail View Endpoint*

  * **As** an end-user
  * **I want** to fetch a single company’s full profile and snapshot history
  * **So that** I can view timeline and changes
  * **Acceptance Criteria:**

    * Endpoint `GET /companies/{id}` returns data + `snapshots[]`.
    * Data fields match Airtable schema.

* **US-5.3** — *Analytics Aggregations*

  * **As** a data analyst
  * **I want** precomputed KPIs (counts, sums, distributions) from ZeroDB
  * **So that** the dashboard Overview loads quickly
  * **Acceptance Criteria:**

    * Endpoints return “total\_startups,” “funding\_sum,” “stage\_breakdown,” etc.
    * Values are accurate against current data set.

---

## Epic 6: Observability & Alerting

**Goal:** Provide visibility into agent health, errors, and performance.

* **US-6.1** — *Health Check Endpoint*

  * **As** an Ops engineer
  * **I want** `/healthz` reporting status of scheduler, scrapers, and API clients
  * **So that** I can integrate with uptime monitors
  * **Acceptance Criteria:**

    * Returns 200 OK when all subsystems are healthy.
    * Returns 500 if any critical dependency is failing.

* **US-6.2** — *Error Logging & Dashboard*

  * **As** a developer
  * **I want** all errors sent to Sentry (or ELK) with context
  * **So that** I can debug failures quickly
  * **Acceptance Criteria:**

    * Scrape failures, API errors, diff issues captured with stack traces.
    * Logs include `company_id`, `source`, and `error_message`.

* **US-6.3** — *Failure Alerts*

  * **As** a program manager
  * **I want** Slack/email notifications when > X% of scrapes fail in an hour
  * **So that** I’m aware of systemic issues
  * **Acceptance Criteria:**

    * Threshold configurable in settings.
    * Alerts include summary of failures and timestamps.

---

## Epic 7: Security & Performance Hardening

**Goal:** Scale the agent securely, ensuring data protection and throughput.

* **US-7.1** — *Rate Limiting & Backoff*

  * **As** a scraper
  * **I want** to respect API rate limits with exponential backoff
  * **So that** I avoid bans and throttling
  * **Acceptance Criteria:**

    * Configurable rate limits per source.
    * Retries with incremental delays up to a max.

* **US-7.2** — *Load Testing*

  * **As** a QA engineer
  * **I want** to simulate syncing 1,000 companies in one run
  * **So that** I can validate performance targets
  * **Acceptance Criteria:**

    * Completed run in under target throughput (e.g., 10 minutes).
    * No memory leaks or unhandled errors.

* **US-7.3** — *Secrets Rotation*

  * **As** a security officer
  * **I want** API keys rotated every 90 days
  * **So that** we minimize risk of leaked credentials
  * **Acceptance Criteria:**

    * Rotation process documented and automated (where possible).
    * Agent fails gracefully when keys expire, with clear logs.

---

## Epic 8: Documentation & Handoff

**Goal:** Ensure smooth onboarding for future maintainers and users.

* **US-8.1** — *Technical Documentation*

  * **As** a new engineer
  * **I want** README, architecture diagrams, and API docs
  * **So that** I can understand, run, and extend the system
  * **Acceptance Criteria:**

    * Contains setup guide, deployment steps, runbook, and code overview.

* **US-8.2** — *User Guide*

  * **As** a program manager
  * **I want** a step-by-step manual for connecting Airtable & Zapier, and using the dashboard
  * **So that** non-technical staff can onboard themselves
  * **Acceptance Criteria:**

    * Screenshots or screencasts of Zapier setup.
    * Instructions on reading analytics and exporting data.

* **US-8.3** — *Knowledge Transfer*

  * **As** a product owner
  * **I want** a recorded demo and handoff session
  * **So that** the team can maintain and evolve the agent smoothly
  * **Acceptance Criteria:**

    * Demo covers end-to-end flow: scrape → diff → update → dashboard.
    * Q\&A documented.

---
