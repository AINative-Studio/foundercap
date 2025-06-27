# Data Model: Startup Funding Tracker & Dashboard

This document defines the detailed, normalized data model to support both Airtable and AINative ZeroDB for the Startup Funding Tracker.

---

## Entities & Attributes

### 1. Company

* **company\_id** (UUID, PK)
* **name** (string, required)
* **logo\_url** (string, URL)
* **operating\_status** (enum: Active, Paused, Exited)
* **website** (string, URL)
* **batch** (string)
* **location** (string)
* **industry** (string)
* **description** (text)
* **linkedin\_url** (string, URL)
* **twitter\_handle** (string)
* **crunchbase\_link** (string, URL)
* **contact\_email** (string, email)
* **notes** (text)
* **total\_funding** (number, USD)
* **funding\_stage** (enum: Pre-Seed, Seed, Series A, Series B, …)
* **acquired\_by** (string, nullable)
* **created\_at** (datetime)
* **updated\_at** (datetime)

### 2. Founder

* **founder\_id** (UUID, PK)
* **first\_name** (string)
* **last\_name** (string)
* **email** (string, email)
* **linkedin\_url** (string, URL)
* **twitter\_handle** (string)
* **diversity\_spotlight** (enum: Women, BIPOC, LGBTQ+, Disability, Veteran, Other)
* **created\_at** (datetime)
* **updated\_at** (datetime)

### 3. Investor

* **investor\_id** (UUID, PK)
* **name** (string)
* **type** (enum: Angel, VC, Corporate)
* **linkedin\_url** (string, URL)
* **contact\_email** (string, email)
* **notes** (text)
* **created\_at** (datetime)
* **updated\_at** (datetime)

### 4. Accelerator

* **accelerator\_id** (UUID, PK)
* **name** (string)
* **website** (string, URL)
* **contact\_email** (string, email)
* **notes** (text)
* **created\_at** (datetime)
* **updated\_at** (datetime)

### 5. Snapshot

* **snapshot\_id** (UUID, PK)
* **company\_id** (UUID, FK → Company)
* **timestamp** (datetime)
* **data** (JSON object capturing all Company fields at this point)

---

## Relationships & Join Tables

### Company ↔ Founder (Many-to-Many)

**CompanyFounder** join table:

* **company\_id** (UUID, FK → Company)
* **founder\_id** (UUID, FK → Founder)
* **role** (string, e.g., CEO, CTO)

### Company ↔ Investor (Many-to-Many)

**CompanyInvestor** join table:

* **company\_id** (UUID, FK → Company)
* **investor\_id** (UUID, FK → Investor)
* **amount\_invested** (number, USD)
* **investment\_date** (datetime)

### Company ↔ Accelerator (Many-to-Many)

**CompanyAccelerator** join table:

* **company\_id** (UUID, FK → Company)
* **accelerator\_id** (UUID, FK → Accelerator)
* **cohort** (string, e.g., "Batch 5")
* **start\_date** (datetime)
* **end\_date** (datetime)

### Company → Snapshot (One-to-Many)

* A Company can have multiple Snapshots capturing historical states.

---

## Storage in Airtable & ZeroDB

* **Airtable:**

  * Each entity corresponds to a table with linked record fields for join relationships.
  * Snapshot data stored in a separate table with JSON field and timestamp.

* **ZeroDB:**

  * Company documents embed related Founder, Investor, Accelerator lists and maintain snapshots array.
  * Query vectors stored at the root of each Company document for similarity search.
