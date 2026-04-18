# Maya Portfolio Manager Architecture

## Overview

Maya Portfolio Manager is being rebuilt from a legacy Flask + SQLAlchemy application into a monorepo with:

- FastAPI backend
- React frontend
- MUI component library
- PostgreSQL as the primary database

The new architecture is intended to preserve proven operational behavior from the legacy system while creating a more maintainable, testable, and scalable foundation for lease portfolio management.

This document explains the architectural direction behind the new application, including where we are intentionally carrying legacy concepts forward and where we are explicitly drawing a line.

## Architectural Goals

### 1. Support operational lease management, not just data entry

The system must handle real portfolio workflows:

- searching by multiple business identifiers
- creating leases with linked customers and assets
- editing schedules after initial creation
- recalculating metrics from current lease state
- tracking changes that affect future cash flows

### 2. Separate business rules from UI behavior

The legacy app mixes route handlers, data access, and business calculations. The new system should isolate:

- API transport concerns
- domain services and calculations
- persistence models
- frontend presentation and interaction logic

### 3. Make schedule logic explicit

The most important architectural decision in this system is that lease schedules are not represented by a single structure. We need both recurring payment intent and editable payment rows. The architecture should treat this as a first-class design choice, not as duplication to be removed.

### 4. Prefer PostgreSQL-native correctness

SQLite helped the legacy system move quickly, but the new application should target PostgreSQL semantics from the start:

- stricter constraints
- better indexing options
- stronger transactional behavior
- room for future reporting and import workloads

## Monorepo Structure

## Repository Shape

- `backend/`
- `frontend/`
- `reference/legacy_flask/portfolio_v2/`
- `docs/`

### Why a Monorepo

The monorepo supports the way this project will actually evolve:

- backend and frontend can share one planning surface
- schema changes and UI changes can land together
- migration work can reference the legacy app without mixing old and new runtime code
- documentation can live beside implementation rather than in a disconnected location

This is a practical choice for a product where domain design is still being refined while implementation starts.

## Backend Architecture

## Backend Role

The FastAPI backend owns:

- API contracts
- validation
- domain orchestration
- calculations
- persistence
- search query behavior

It should not become a thin CRUD wrapper. Business rules such as schedule generation, last payment date calculation, cash flow production, and asset removal effects belong in backend domain services.

## Suggested Backend Layers

### API Layer

Responsibilities:

- request routing
- authentication and authorization later
- response shaping
- input validation handoff

Examples:

- customer suggestion endpoint
- lease list and search endpoint
- lease create endpoint
- lease detail endpoint
- lease update endpoint in V1

### Schema Layer

Responsibilities:

- request and response models
- explicit contracts between frontend and backend
- separation of transport shape from ORM entities

This is especially important for lease creation and editing, where the UI may submit nested customer, financial, asset, and schedule payloads that should not map one-to-one onto database tables.

### Domain Service Layer

Responsibilities:

- lease creation orchestration
- schedule generation
- payment step condensation
- lease metric calculation
- last payment date logic
- asset removal handling
- future payment reduction rules

This is the most important backend layer from a maintainability standpoint. The domain service layer is where we prevent the new application from drifting back into route-level business logic.

### Persistence Layer

Responsibilities:

- SQLAlchemy models
- repository-style data access if needed
- transaction boundaries
- query optimization

We should avoid burying business rules inside model methods where behavior becomes hard to test in isolation.

## Frontend Architecture

## Frontend Role

The React + MUI frontend owns:

- workflow orchestration for users
- search interaction
- forms and validation feedback
- lease detail presentation
- row editing experience for schedules
- dashboards and summary views

The frontend should remain stateful enough to support rich workflows, but calculations that determine business truth should stay on the backend.

## Core Frontend Screens

### MVP

- lease list with search and filters
- lease create flow
- inline customer create within lease create
- lease detail view

### V1

- lease edit flow
- asset edit flow
- dashboard KPI view

## Frontend Interaction Principles

### Search should be fast and forgiving

Users should not need to know whether they are searching a lease field, a customer field, or an asset field. The UI should present one clear search entry point while the backend handles the multi-field query logic.

### Suggestion UX should reduce duplicates

Customer suggestions should appear after a few typed characters, not on every keystroke from the first character. That threshold reduces noise and keeps the list useful.

### Editable schedules need careful UX boundaries

If the schedule is the row-level truth for the UI, then the UI must make it obvious when the user is:

- editing generated rows
- replacing the full schedule
- making changes that will affect metrics

Users should not have to infer whether they are changing a pattern or changing actual cash flow rows.

## Data Flow for Core Workflows

## Lease Creation Flow

1. User starts lease creation.
2. Frontend queries customer suggestions after the search input crosses the configured threshold.
3. User selects an existing customer or creates a new one inline.
4. User enters lease, financial, asset, and payment inputs.
5. Frontend submits a structured create request.
6. Backend validates payload consistency.
7. Backend creates:
   - lease record
   - financial info record
   - asset records
   - payment steps
   - generated lease payment schedule rows
8. Backend computes or persists derived fields such as last payment date.
9. Frontend navigates to lease detail.

## Lease Detail Flow

1. Frontend requests a composed lease detail view.
2. Backend loads lease, customer, financial info, assets, and future schedule rows.
3. Backend calculates lease metrics from current schedule state.
4. Frontend renders a read-optimized detail view.

## Lease Edit Flow

1. Frontend loads the current editable lease state.
2. User edits lease, asset, or schedule data.
3. Backend applies business rules based on edit type.
4. If the schedule is replaced, dependent schedule data is regenerated or replaced consistently.
5. Metrics and derived dates are recalculated from the post-edit state.

## Search Architecture

## Search Requirements

Search must support:

- lease number
- VIN or serial
- customer name
- customer code or number

## Architectural Implications

This requirement should shape the schema and query layer:

- customer search fields need normalized text support
- asset identifiers need indexed lookup
- lease list queries will likely join or use indexed denormalized fields
- exact-match and partial-match behavior should be intentional, not accidental

## Recommended Search Direction

For the first version:

- keep search logic in backend query services
- use normalized fields where helpful, such as a `search_name` style customer field
- index frequently searched columns in PostgreSQL
- prefer one portfolio search entry point instead of separate search features per entity

Later, if needed, this can evolve into dedicated search documents or PostgreSQL full-text support. That is not required for the initial release.

## Schedule Modeling Strategy

## Why We Keep Two Structures

The project has already made the right call to keep both:

- `payment_steps`
- `lease_payment_schedules`

These are not redundant tables serving the same purpose.

### `payment_steps`

Role:

- captures the intended recurring payment structure
- compact representation of schedule logic
- useful for creation, regeneration, and condensation

### `lease_payment_schedules`

Role:

- captures actual dated rows used by the UI
- supports row-level edits
- supports calculations after edits
- represents the lease as currently experienced operationally

## Architectural Consequence

Any service that mutates schedules must define which artifact it is updating:

- pattern definition
- actual row set
- both

This explicitness will prevent subtle data corruption and make later reconciliation tools easier to build.

## Metrics and Calculation Architecture

## Backend-Owned Metrics

The backend should own:

- cash flow generation
- IRR calculation
- NPV calculation
- remaining term
- remaining total
- last payment date logic

These outputs belong on the backend because:

- they define business truth
- they need consistent reuse across screens and exports
- they depend on validated lease state

## Calculation Inputs

Metric services should use:

- current lease financials
- current schedule rows
- current date
- active business rules for future or inactive assets

They should avoid depending on stale summary fields that can drift from schedule reality.

## Change and Audit Architecture

## Why Audit Matters Here

The project includes behaviors such as:

- schedule replacement
- partial asset removal
- future payment reduction
- inactive asset logging

These are change events with business meaning, not routine field edits.

## Architectural Direction

The first release does not need a fully generalized event-sourcing model, but it should preserve meaningful history through explicit tables and write paths:

- inactive asset logs
- timestamps on mutable records
- clear separation between active and historical records where needed

This gives the product a practical audit foundation without overengineering the first implementation.

## Migration Boundary with the Legacy System

## What We Reuse Conceptually

We should retain proven domain concepts from the legacy app:

- customer suggestion flow
- multi-key portfolio search
- lease metrics
- dual schedule representation
- inactive asset logging pattern

## What We Are Not Carrying Forward Automatically

- route-level business logic
- import-time Net Cap Cost calculation
- legacy schedule compatibility behavior
- accidental coupling created by the Flask app's implementation shortcuts

The new system should reuse business intent, not implementation debt.

## Non-Goals for the Initial Architecture

- no attempt to preserve every legacy edge case at runtime
- no premature microservice split
- no frontend-owned business calculations as the source of truth
- no import framework in the core runtime before the base product model is stable

## Expected Evolution

The architecture should support a phased delivery path:

### Phase 1

- establish core entities and search
- lease creation
- lease detail
- metric calculation

### Phase 2

- controlled editing
- schedule replacement and condensation
- asset lifecycle handling
- dashboard KPIs

### Phase 3

- CSV import and deduplication
- verification and reconciliation utilities
- richer reporting

That sequence matters. The system should first become operationally correct at the record level before broadening into ingestion and analytics.

## Architecture Summary

Maya Portfolio Manager should be built as a domain-centered monorepo application where:

- FastAPI owns business truth and calculation logic
- React + MUI provide efficient operational workflows
- PostgreSQL enforces a stronger data model
- search is designed around real business identifiers
- schedules are modeled as both pattern definitions and actual editable rows
- migration decisions are based on business value, not legacy parity for its own sake

If this architecture stays disciplined around those points, it will support both the MVP and the more complex V1 and import-oriented phases without forcing another structural rewrite.
