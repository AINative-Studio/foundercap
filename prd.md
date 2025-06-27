**Product Requirements Document**

**Project:** Startup Funding Tracker & Dashboard Automation
**Date:** June 27, 2025
**Author:** \[Your Name]

---

### 1. Executive Summary

A web-based dashboard and automated agent designed for a nonprofit supporting underrepresented founders in the US. The system will track startups, monitor funding and status updates from LinkedIn, Crunchbase, and Google Alerts, then synchronize to Airtable (source of truth) and ZeroDB (optimized data store) via Zapier and ZeroDB APIs. This PRD outlines features, data model, architecture, and implementation plan.

### 2. Objectives & Goals

* **Automate Data Capture:** Continuously fetch updates on startups from multiple sources.
* **Centralize Information:** Store authoritative data in Airtable and maintain enriched, query-optimized records in ZeroDB.
* **Visualize Insights:** Provide staff with a dashboard for filtering, sorting, and analyzing key metrics.
* **Ensure Accuracy:** Detect and apply only meaningful changes to minimize noise.
* **Maintain Security & Compliance:** Securely handle API credentials and PII (emails).

### 3. Stakeholders

* **Product Owner:** Nonprofit Leadership
* **End Users:** Program Managers, Outreach Coordinators, Data Analysts
* **Technical Team:** Backend Engineers, Frontend Developers, DevOps
* **Integrations:** Airtable Admin, Zapier Accounts, LinkedIn API, Crunchbase API, ZeroDB API

### 4. Scope & Features

#### 4.1 Data Fields (Airtable & ZeroDB Schema)

* Company
* Logo URL
* Operating Status
* Website
* Batch
* Founder(s)
* Diversity Spotlight
* Location (City, State)
* Industry
* Description
* LinkedIn URL
* Twitter Handle
* Contact Email
* Notes
* Total Funding
* Funding Stage
* Investors
* Accelerators
* Acquired By
* Crunchbase Link
* **Hidden**: lastChecked timestamp per source
* **ZeroDB-only**: Query vectors, historical snapshots

#### 4.2 Dashboard Features

* **Table View:** Columns matching Airtable fields, with search, filter, sort, bulk actions via ZeroDB queries
* **Detail Panel:** Expanded view with full description, timeline, external links, data fetched from ZeroDB snapshot store
* **Analytics Overview:** KPI cards (total startups, diversity breakdown, funding distribution), charts (bar, line, map, funnel) sourced from ZeroDB aggregates
* **Admin Settings:** Zapier ↔ Airtable mapping, ZeroDB API credentials, sync frequency
* **Notifications:** Alert on scrape failures or critical changes (e.g., acquisition)

#### 4.3 Scraper/Agent Features

* **Sources:** LinkedIn, Crunchbase, Google Alerts (RSS)
* **Scheduling:** Configurable cron (default hourly)
* **Change Detection:** Compare fetched data vs. snapshot stored in ZeroDB; produce diff
* **Airtable Updater:** PATCH only changed fields via REST API
* **ZeroDB Updater:** Use ZeroDB write API to upsert enriched records and snapshots
* **Cache Invalidation:** Trigger dashboard backend refresh per company via ZeroDB cache invalidation API
* **Logging:** Centralized logs with error alerts (Slack or email)

### 5. User Flows

1. **Initial Setup:** Admin connects Airtable base via Zapier; configures ZeroDB API credentials; imports existing records into ZeroDB.
2. **Automated Sync:** Scheduler fires; agent fetches updates; diffs against ZeroDB snapshots; patches Airtable; upserts to ZeroDB; invalidates dashboard cache.
3. **Data Review:** Staff log into dashboard; filter via ZeroDB-powered search; view details.
4. **Outreach & Reporting:** Export filtered lists; generate PDF reports; share KPIs in board meetings.

### 6. Data Model & API Contracts

This section maps our data entities to both Airtable and AINative ZeroDB API endpoints defined in the OpenAPI spec (available at `https://api.ainative.studio/api/v1/openapi.json`).

#### 6.1 Airtable Record Example

```json
{
  "id": "rec123...",
  "fields": {
    "Company": "Acme Co",
    "Operating Status": "Active",
    "Total Funding": 2300000,
    "Funding Stage": "Series A",
    "Investors": ["VC A","Angel B"],
    // ... other fields
  }
}
```

#### 6.2 ZeroDB Record Schema

ZeroDB stores an enriched document model with versioned snapshots and query vectors.

```json
{
  "id": "company_123",
  "data": {
    "Company": "Acme Co",
    "Operating Status": "Active",
    "Total Funding": 2300000,
    "Funding Stage": "Series A",
    "Investors": ["VC A","Angel B"],
    // ... other fields mirrored from Airtable
  },
  "snapshots": [
    { "timestamp": "2025-06-27T12:00:00Z", "data": { /* initial load */ } },
    { "timestamp": "2025-06-27T13:00:00Z", "data": { /* post-update */ } }
  ],
  "queryVector": [0.12, -0.05, ...]
}
```

#### 6.3 ZeroDB API Endpoints

Leverage the AINative ZeroDB OpenAPI spec to interact with records and caching:

| Operation            | HTTP Method & Path              | Description                                                         |
| -------------------- | ------------------------------- | ------------------------------------------------------------------- |
| List Records         | `GET /api/v1/records`           | Retrieve paginated list of ZeroDB records.                          |
| Get Record by ID     | `GET /api/v1/records/{id}`      | Fetch a single record with snapshots and vector data.               |
| Create/Upsert Record | `POST /api/v1/records`          | Insert or update a record; body accepts full `data` payload.        |
| Update Record Fields | `PATCH /api/v1/records/{id}`    | Partial update of record fields.                                    |
| Delete Record        | `DELETE /api/v1/records/{id}`   | Remove a record from ZeroDB.                                        |
| Invalidate Cache     | `POST /api/v1/cache/invalidate` | Invalidate cached entries for one or more record IDs.               |
| Search Records       | `POST /api/v1/records/search`   | Full-text & vector similarity search; accepts query or vector input |

> **Note**: Full parameter and response schemas can be referenced in the OpenAPI specification.

#### 6.4 Example ZeroDB Integration (Python)

```python
from ainative import ZeroDBClient

client = ZeroDBClient(
    api_key="<YOUR_ZERO_DB_API_KEY>",
    base_url="https://api.ainative.studio/api/v1"
)

def upsert_company(record_id, payload):
    """Creates or updates a ZeroDB record with enriched data."""
    body = { "id": record_id, "data": payload }
    resp = client.post("/records", json=body)
    resp.raise_for_status()
    return resp.json()


def invalidate_company_cache(record_id):
    """Clears cached queries related to this company."""
    body = { "recordIds": [record_id] }
    resp = client.post("/cache/invalidate", json=body)
    resp.raise_for_status()
    return resp.json()
```

### 7. Technical Architecture Technical Architecture

```
[ Scheduler (Celery / cron ) ]
          |
   [ Scraper Modules ] ← LinkedIn API / Puppeteer
          |        ← Crunchbase API / BeautifulSoup
          |        ← Google Alerts RSS → Zapier Webhook
          v
[ Diff & Updater ] → Airtable REST API
          |       → ZeroDB Write API (upsert snapshots & enriched data)
          |       → ZeroDB Cache Invalidation API
          |
   [ZeroDB (primary query store, snapshot history)]
          |
   [Dashboard Backend: FastAPI + ZeroDB Read API]
          |
   [Dashboard Frontend: React + Tailwind + ZeroDB SDK]
```

#### 7.1 Technology Stack

* **Backend:** Python (FastAPI + Celery) or Node.js (Express + Bull)
* **Scraping:** Playwright (LinkedIn), requests+BeautifulSoup (Crunchbase)
* **Primary Stores:** Airtable (authoritative), ZeroDB (enriched store & search)
* **Cache:** Built into ZeroDB with TTL and invalidation API
* **Frontend:** React, Tailwind CSS, Recharts, ZeroDB JS SDK
* **Integration:** Zapier Webhooks, ZeroDB API Key Vault (AWS Secrets Manager)
* **Hosting:** AWS ECS/Fargate or Heroku Docker

### 8. Non-Functional Requirements

* **Performance:** Full sync of 100 records within 5 mins; ZeroDB queries <200ms
* **Reliability:** 99.9% uptime; retry logic on transient failures
* **Security:** TLS everywhere; secure storage of API keys; audit logs
* **Scalability:** Handle up to 10K companies in future; horizontal scaling of ZeroDB cluster
* **Maintainability:** Modular code, unit tests (pytest/jest), CI/CD

### 9. Milestones & Timeline

| Sprint | Deliverables                                         | Duration  |
| ------ | ---------------------------------------------------- | --------- |
| 1      | PRD sign-off, Airtable + ZeroDB schema, Zapier setup | 1 week    |
| 2      | Scraper prototype (Crunchbase → Airtable & ZeroDB)   | 2 weeks   |
| 3      | LinkedIn module, diff logic, full scheduler          | 2 weeks   |
| 4      | Dashboard MVP (table & detail via ZeroDB reads)      | 2 weeks   |
| 5      | Analytics page, cache invalidation, logging          | 2 weeks   |
| 6      | Testing, error handling, deployment                  | 1 week    |
|        | **Total**                                            | **10wks** |

### 10. Risks & Mitigations

* **API Rate Limits:** Batch requests; implement backoff.
* **Scraper Breakage:** Monitor CSS selector failures; fallback to API where possible.
* **Data Inconsistencies:** Validate fetched data; manual review flags.
* **Security Breach:** Rotate keys regularly; least-privilege IAM.

---

**Approval:**

* Product Owner: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  Date: \_\_\_\_\_\_
* Engineering Lead: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  Date: \_\_\_\_\_\_
* QA Lead: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  Date: \_\_\_\_\_\_
