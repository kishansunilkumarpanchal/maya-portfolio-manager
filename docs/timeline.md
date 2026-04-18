# Maya Portfolio Manager Delivery Timeline

## Purpose

This timeline is a delivery sequence for the new Maya Portfolio Manager application. It is not a date-committed roadmap. The point is to show implementation order, dependencies, and the reasoning behind that order so work stays aligned with the actual product risks.

The guiding principle is simple: establish record-level correctness first, then controlled editing, then migration and analytics depth.

## Delivery Strategy

### Phase Ordering

1. Foundation and domain skeleton
2. MVP operational workflows
3. V1 editing and portfolio operations
4. Import, reconciliation, and expanded analytics

This order reflects the project's real dependency chain. Search, lease creation, schedule representation, and metrics have to be stable before dashboarding or import automation can be trusted.

## Phase 0: Foundation

### Objectives

- establish the monorepo working structure
- set up FastAPI backend scaffold
- reserve React frontend workspace
- preserve the legacy Flask application as a reference source
- create the planning and architecture documentation base

### Outcome

The team has a clean project shell, a preserved legacy reference, and a documented direction for new implementation.

### Why This Comes First

Without a clear project skeleton and documented scope, migration work tends to become a loose series of ports instead of a deliberate rebuild.

## Phase 1: Core Data Model and Search Foundations

### Objectives

- implement core reference data models
- implement customers, leases, financial info, assets
- implement `payment_steps`
- implement `lease_payment_schedules`
- establish indexing and query patterns for search

### Key Deliverables

- PostgreSQL-ready schema definitions
- migration files for core tables
- backend models and schemas
- initial query services for customer suggestions and lease search

### Critical Decisions Exercised Here

- search across lease number, VIN or serial, customer name, and customer code or number
- keeping both payment pattern and actual schedule rows
- establishing last payment date behavior in the model

### Why This Comes Before UI Completion

The UI depends on clear entity boundaries. Search and lease workflows will move faster once the schema and service contracts are stable.

## Phase 2: MVP Lease Intake and Portfolio Navigation

### Objectives

- deliver customer suggestion behavior
- deliver lease creation
- deliver inline customer creation
- deliver lease list with search and filters
- deliver lease detail

### Key Deliverables

- customer suggestion endpoint and frontend interaction
- create-lease API and frontend flow
- customer create API pathway usable from the lease flow
- lease list screen with operational search
- lease detail screen showing customer, financial, asset, schedule, and metric information

### Dependencies

- core data model from Phase 1
- stable search query behavior
- initial schedule generation services

### Definition of Done

An operations user can:

- locate a lease by the identifiers they actually have
- create a new lease without relying on the legacy app
- add a missing customer inline
- open the lease and review its current data confidently

## Phase 3: MVP Calculations and Schedule Confidence

### Objectives

- complete cash flow generation behavior
- calculate IRR, NPV, remaining term, and remaining totals
- lock down last payment date logic
- confirm schedule generation from payment steps is reliable

### Key Deliverables

- backend calculation services
- test coverage around schedule and metric calculations
- lease detail metrics grounded in current schedule data

### Why This Is Broken Out Explicitly

The product can superficially look complete before its numbers are trustworthy. This phase exists to make sure the system is not only navigable, but financially credible.

## Phase 4: V1 Editing Foundations

### Objectives

- enable lease editing
- enable schedule replacement
- enable schedule condensing
- enable asset editing
- enable asset status updates

### Key Deliverables

- edit-lease API contracts
- edit-focused frontend forms
- backend services for controlled schedule replacement
- condensation logic from detailed rows back to payment steps where appropriate

### Risks Managed Here

- drift between recurring payment intent and actual schedule rows
- accidental destructive overwrites during lease edits
- unclear recalculation behavior after edits

### Why This Is After MVP Read-Only Confidence

Editing introduces much more risk than creation. It should follow, not precede, confidence in the base schedule and metric model.

## Phase 5: V1 Asset Lifecycle and Adjustment Logic

### Objectives

- support partial asset removal
- reduce future payments when lease economics change
- log inactive assets and their financial effect

### Key Deliverables

- inactive asset log table and services
- future-payment reduction rules
- asset removal UI and validation behavior

### Why This Is Its Own Phase

This is the point where the application starts handling meaningful lease-change events rather than only static records. It deserves focused design and testing because it affects history, current state, and future cash flows simultaneously.

## Phase 6: V1 Dashboard KPIs

### Objectives

- add portfolio-level summary views
- expose useful operational KPIs

### Key Deliverables

- dashboard APIs
- KPI cards and summary views in the frontend
- validated definitions for each KPI shown

### Why This Waits

Dashboard numbers are downstream outputs. They should only be introduced after the underlying lease, asset, and schedule behaviors are stable enough to support them.

## Phase 7: Import and Migration Utilities

### Objectives

- build CSV import pipeline
- add duplicate-safe behavior
- add asset ID compatibility helpers

### Key Deliverables

- import staging logic
- matching and deduplication rules
- operator-friendly validation feedback

### Why This Is Later

Import is where legacy edge cases and data-quality problems show up most aggressively. It should be built against a settled domain model, not while the core model is still shifting.

## Phase 8: Verification, Reconciliation, and Richer Reporting

### Objectives

- build verification and reconciliation utilities
- add broader analytics and reporting

### Key Deliverables

- tools to compare imported and calculated values
- operational audit and review support
- richer reporting surfaces for portfolio analysis

### Why This Is the Final Planned Phase

These tools become genuinely useful only when the core application, editing model, and import pipeline are already reliable.

## Cross-Cutting Workstreams

These run throughout the timeline rather than belonging to a single phase.

### Testing

- unit tests for calculation services
- integration tests for create, search, and edit workflows
- regression coverage around schedule replacement and asset removal

### Data Quality

- normalization rules for search fields
- validation of status values and identifiers
- careful handling of nullable legacy fields during migration

### Documentation

- keep scope and architecture docs current as implementation clarifies them
- log meaningful decisions as they are accepted or revised

## What This Timeline Intentionally Avoids

- no early investment in legacy compatibility behavior that the new model does not need
- no import-first approach before operational workflows are stable
- no dashboard-first approach before record-level correctness exists
- no attempt to overcommit dates before implementation velocity is known

## Expected Near-Term Path

If work starts immediately, the cleanest near-term sequence is:

1. finalize schema direction for customers, leases, financial info, assets, payment steps, and schedule rows
2. implement search and customer suggestion behavior
3. implement lease creation with inline customer creation
4. implement lease detail with schedule-backed metrics
5. expand into edit and asset lifecycle logic

This sequence follows the actual shape of the product and avoids burning time on downstream concerns before the core lease model is trustworthy.
