# Maya Portfolio Manager Schema Thinking

## Purpose

This document explains the database design direction for Maya Portfolio Manager. It is intentionally more about modeling decisions than final DDL. The immediate goal is to make sure the PostgreSQL schema reflects the actual lease portfolio domain and the project decisions already made during planning.

The system is moving from a legacy SQLAlchemy model used with SQLite and PostgreSQL toward a PostgreSQL-first design in the new FastAPI application. That shift is an opportunity to clarify ownership, constraints, and query patterns before implementation hardens.

## Design Objectives

### 1. Model the business, not just the forms

The schema needs to support:

- operational search
- lease entry
- row-level schedule editing
- financial calculations
- asset lifecycle changes
- future import and reconciliation work

### 2. Keep creation-time structure separate from runtime reality

One of the main lessons from the legacy app is that recurring payment intent and the actual editable schedule cannot be collapsed into one table without losing meaning.

### 3. Prefer explicitness over magical derivation

Fields that are used operationally, searched frequently, or shown repeatedly should be intentionally stored or generated rather than reassembled inconsistently across the codebase.

## Proposed Core Entity Areas

## Reference Data

Reference tables should stay small, explicit, and constrained. They support consistency across operational data.

Likely tables:

- `provinces` or equivalent geography reference
- `asset_groups`
- `tax_rates`
- additional lookup tables only where they materially improve consistency

Why reference tables matter here:

- they reduce free-text drift in forms
- they support reporting and filtering later
- they keep imports easier to validate

## Customers

Customers are first-class entities and should not be treated as simple text blobs attached to leases.

### Core fields

- primary key
- customer code or customer number
- company name
- first name
- middle name
- last name
- trade name
- address fields
- city
- province reference
- postal code
- normalized search field or fields
- timestamps

### Important modeling notes

#### Customer code must remain searchable

The project already decided that customer code or number is part of portfolio search. That means it is not just descriptive metadata. It needs:

- indexing
- validation rules
- consistent normalization

#### Search name is still useful

The legacy app used a `search_name` field composed from company and personal name fragments plus customer code. The exact implementation can improve, but the concept is still valuable. A normalized customer search field will simplify suggestion queries and lease list search behavior.

## Leases

Leases are the primary operational aggregate in the system.

### Core fields

- primary key
- customer foreign key
- lease number
- funding date
- payment start date
- total terms
- interest rate
- status
- tax code or tax reference
- last payment date
- timestamps

### Important modeling notes

#### Lease number must be unique

This is the most important human-readable identifier in the system and should be protected accordingly.

#### Last payment date should be treated as a derived operational field

The project includes explicit last payment date logic in scope. Even if it is derivable, it is valuable enough operationally to store and keep in sync, provided that the write path for recalculation is controlled.

This field matters because it is:

- shown in detail views
- useful in filters and reports
- part of user trust in the record

## Financial Info

Financial data is best modeled as a one-to-one extension of the lease record rather than flattened entirely into the lease table.

### Core fields

- lease foreign key as primary key or unique foreign key
- capital cost
- cap cost adjustment
- down payment
- trade amount
- net cap cost
- lessee residual
- lessor residual
- monthly depreciation
- monthly payment
- security deposit
- timestamps

### Why separate financial info

- keeps the core lease record focused
- groups financial inputs together for validation and service logic
- mirrors the real workflow structure of lease entry and review

### Scope note on Net Cap Cost

The project has explicitly removed Net Cap Cost import calculation from current scope. That should influence service logic, not necessarily schema existence. We can still store `net_cap_cost` if it is operationally useful, but we should not embed opaque legacy import rules into the schema design.

## Assets

Assets belong to a lease and are central to both search and downstream adjustment logic.

### Core fields

- primary key
- lease foreign key
- asset group foreign key
- asset identifier
- year
- make/model
- VIN or serial
- finance source
- equipment cost
- percentage value
- status
- timestamps

### Important modeling notes

#### VIN or serial is a search key

The user requirement already makes VIN or serial part of global search. This means it needs:

- indexing
- normalized comparison behavior
- clear constraints around nullability and expected uniqueness assumptions

Not every asset identifier is guaranteed globally unique in messy real-world data, so we should avoid prematurely enforcing uniqueness on VIN or serial without reviewing actual portfolio quality.

#### Asset identifier compatibility is a later concern

The legacy app generated asset IDs from lease number and VIN fragments. Since asset ID compatibility helpers are explicitly later-scope, the base schema should not overfit to that generated pattern. It should preserve space for a canonical asset identifier without locking the system into old generation logic.

#### Asset status is not cosmetic

Status affects whether an asset is active in the current lease picture, and it relates directly to inactive asset logs and future payment reduction behavior.

## Payment Steps

`payment_steps` represent the structured payment pattern definition for a lease.

### Core fields

- primary key
- lease foreign key
- start date
- amount
- frequency
- number of payments
- payment type
- ordering or sequence metadata if needed
- timestamps

### Why this table exists

This table is the compact, interpretable representation of how the lease was intended to bill. It supports:

- initial schedule generation
- regeneration after controlled edits
- condensation of detailed rows back into step patterns

### What this table should not try to do

It should not be forced to represent every row-level exception after manual edits. Once the schedule diverges from the recurring pattern, the actual schedule rows carry the operational truth.

## Lease Payment Schedules

`lease_payment_schedules` represent actual dated payment rows.

### Core fields

- primary key
- lease foreign key
- payment date
- amount
- period number
- payment type
- timestamps

### Why this table exists

This table is required because the UI and calculations need a row-level representation that supports:

- direct editing
- future-only reductions
- recalculation after adjustments
- detailed display in lease detail and edit screens

### Schema consequence

The existence of this table is not a temporary migration compromise. It is part of the domain model.

## Inactive Asset Logs

Inactive asset logging should remain a distinct table because it captures a business event, not just current state.

### Core fields

- primary key
- asset foreign key
- lease foreign key
- date removed
- original cost
- removed net cap cost
- removed monthly payment
- removed residual
- timestamps

### Why this table matters

When an asset is removed from a lease, the product must preserve the financial effect of that change. The log table provides a straightforward audit record without requiring a full event-sourcing framework.

## Search-Oriented Schema Decisions

## Required Search Inputs

Portfolio search must support:

- lease number
- VIN or serial
- customer name
- customer code or number

## Likely schema support

### Leases

- unique index on `lease_number`

### Customers

- index on `customer_code`
- index or text-search strategy for normalized customer name fields
- potentially a stored normalized `search_name`

### Assets

- index on `vin_serial`

### Query approach

The first implementation can use relational joins and indexed `ILIKE` or normalized comparisons. We do not need to jump directly to a specialized search subsystem.

## Constraints and Integrity Direction

## Prefer PostgreSQL-enforced integrity where reasonable

Examples:

- unique lease number
- foreign key constraints for all core relationships
- not-null constraints on fields that are operationally required
- check constraints where status or frequency values come from controlled sets

## Be careful with over-constraining messy migrated data

The schema should be strict, but it should not assume legacy data is perfect. In areas such as VIN or serial uniqueness, we should validate actual data first before imposing irreversible constraints.

## Derived and Stored Fields

## Candidates to store

- `leases.last_payment_date`
- normalized customer search text
- maybe selected denormalized display fields later if search or reporting needs justify them

## Rule of thumb

Store a derived value when:

- it is queried frequently
- users rely on it directly
- recomputing it everywhere would create inconsistency

Do not store a derived value merely because it was convenient in the legacy app.

## Status Modeling

Status values should be explicit and consistent across entities.

Likely domains:

- lease status
- asset status
- payment type
- payment frequency

These can begin as constrained strings or enums, but the important part is shared meaning across API, schema, and UI. A status field should never exist purely for display styling.

## Temporal and Audit Considerations

The schema should support traceability without overcomplicating the first release.

Recommended baseline:

- `created_at`
- `updated_at`

Recommended where business history matters:

- inactive asset log records
- deliberate write paths for schedule replacement rather than silent in-place mutation without service control

The project may later need richer audit history, but the initial schema should first preserve meaningful state transitions in the areas already known to be sensitive.

## Tables Likely Needed in MVP

- `customers`
- `leases`
- `financial_info`
- `assets`
- `payment_steps`
- `lease_payment_schedules`
- `provinces`
- `asset_groups`
- `tax_rates`

## Tables Likely Needed by V1

- `inactive_asset_logs`
- any optional supporting tables introduced to manage dashboard summarization or controlled schedule edit metadata

## Explicit Non-Goals for Initial Schema Design

- do not design around legacy schedule compatibility
- do not bake import-pipeline assumptions into the operational schema
- do not over-normalize fields that need to be searched simply because normalization looks cleaner on paper
- do not collapse `payment_steps` and `lease_payment_schedules` into one model

## Open Implementation Questions

These are not placeholders for the documentation; they are the real design questions that should be answered when the schema is implemented:

1. Should customer search use a single normalized `search_name` column, PostgreSQL full-text search, or both?
2. Which lease and asset status values should be constrained in the database versus validated in the API layer?
3. How should schedule replacement be tracked if we later need stronger history than current-row mutation plus logs?
4. Which indexes are required immediately for portfolio-scale search performance, and which can wait for observed query patterns?

## Schema Summary

The schema for Maya Portfolio Manager should be built around the lease as the primary aggregate, with clean relationships to customers, financial info, assets, payment steps, and actual payment schedule rows. The most important modeling choice is preserving both schedule intent and row-level schedule reality. If we keep that distinction clear, the rest of the schema can support search, editing, metrics, and later imports without forcing domain compromises.
