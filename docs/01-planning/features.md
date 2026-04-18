# Maya Portfolio Manager Feature Plan

## Purpose

This document captures the intended functional scope for Maya Portfolio Manager as the product moves from a legacy Flask application into a new FastAPI + React monorepo. It is written as a planning artifact, not a marketing summary. The goal is to preserve the business behaviors that matter in day-to-day portfolio management while deliberately narrowing scope where the legacy system contains brittle or low-value complexity.

The application target is a professional-grade lease portfolio management system used to:

- maintain clean customer and lease records
- search the portfolio quickly across multiple business identifiers
- manage asset-backed leases with payment schedules that may change over time
- calculate cash flow metrics used to review lease performance
- support operational edits without destroying historical meaning

## Product Framing

### What We Are Building First

The new application is not a one-to-one rewrite of the legacy Flask app. The first release should preserve the operational core:

- customer and lease intake
- reliable search and lookup
- lease-level financial visibility
- editable payment schedules
- core lease metrics
- asset tracking

### What We Are Explicitly Not Solving Yet

To keep the first release focused and defensible, the following areas are intentionally out of current scope:

- Net Cap Cost import-time calculation
- legacy schedule compatibility behavior
- bulk CSV import and reconciliation workflows
- advanced reporting beyond operational KPIs

These exclusions are not accidental. They remove migration drag and allow the new system to establish clean domain rules before bringing in higher-risk import and compatibility layers.

## Working Product Principles

### 1. Search must feel operational, not decorative

Users do not search by only one identifier. Portfolio staff need to find a lease by whatever piece of information they have at hand. Search must support:

- lease number
- VIN or serial number
- customer name
- customer code or customer number

This affects backend indexing, frontend search UX, and how we shape denormalized search fields.

### 2. Creation flows must minimize context switching

Lease entry is already a high-friction task. The new UI should not force users to leave the workflow just to create a missing customer. Inline customer creation is part of the product scope because it removes a real operational interruption.

### 3. Schedules are not only calculated artifacts

The legacy system exposed a real need: once a lease is active, schedule rows often need manual adjustment. That means a single recurring payment pattern is not sufficient as the source of truth for all downstream workflows. The product must preserve both:

- `payment_steps` as the recurring or structured pattern definition
- `lease_payment_schedules` as actual dated rows used for editing, row-level adjustments, and metric calculations

### 4. Edits must preserve business meaning

Asset removal, payment reductions, and replacement schedules are not simple updates. They change the financial interpretation of a lease. Product behavior in these areas must leave an auditable trail and avoid destructive overwrites where history matters.

## MVP Scope

The MVP is the minimum operational release that can support real lease portfolio usage in the new stack.

### Customers

#### Included

- customer master records
- customer code or number support
- company and person naming fields
- address and province/state references
- normalized search display fields

#### Why It Is In MVP

Customer records sit at the center of lease creation and portfolio search. If customer data is weak, search quality, document fidelity, and lease review all degrade immediately.

### Customer Suggestions and Search

#### Included

- customer suggestion dropdown during lease creation
- suggestion behavior after a few typed characters
- lookup by company name, personal name, and customer code or number
- deterministic selection of an existing customer into the lease form

#### Expected Behavior

- Suggestions appear only after the user has typed enough characters to make the query useful.
- Results should be ordered for operational clarity, not simply database insertion order.
- The UI must make it easy to confirm whether the selected record is the correct customer before saving the lease.

#### Why It Is In MVP

This is not a convenience enhancement. It directly reduces duplicate customers and keeps lease entry efficient.

### Leases

#### Included

- lease master record
- lease number uniqueness
- funding date
- payment start date
- total term
- interest rate
- status
- last payment date logic

#### Why It Is In MVP

The lease record anchors all finance, asset, and schedule behavior. Without a stable lease model, every downstream screen becomes fragile.

### Financial Info

#### Included

- lease-level financial information record
- capital cost and related inputs
- down payment and trade amount
- residual values
- monthly payment
- monthly depreciation
- security deposit

#### Scope Notes

- Net Cap Cost import calculation is intentionally excluded from current scope.
- That does not prevent storing a net cap cost value in the application; it only means we are not taking on legacy import-side calculation behavior as part of MVP.

### Assets

#### Included

- one-to-many asset linkage to a lease
- asset identifying attributes such as year, make/model, and VIN or serial
- equipment cost
- asset grouping or category support through reference data
- asset status field

#### Why It Is In MVP

In this product, a lease is not meaningful without the underlying financed assets. Search also depends on asset identifiers.

### Reference Tables

#### Included

- provinces or states
- asset groups or categories
- tax rate reference data
- other small supporting lookup tables needed to keep lease entry consistent

#### Why It Is In MVP

Reference data removes free-text drift in fields that drive reporting, validation, and search quality.

### Payment Steps

#### Included

- recurring pattern definition for scheduled payments
- step start date
- amount
- frequency
- number of payments
- payment type

#### Product Role

`payment_steps` describe how a lease is intended to bill over time. They are the structured business definition used to generate or regenerate schedule rows.

### Full Payment Schedule

#### Included

- row-level dated schedule entries
- payment date
- amount
- period number
- payment type
- ordering for review and downstream calculations

#### Product Role

`lease_payment_schedules` represent the actual row set the UI shows, edits, and uses for calculations. This table exists because real leases diverge from idealized recurring steps.

### Lease Creation

#### Included

- create lease flow in the new UI
- customer selection
- lease details
- financial inputs
- asset entry
- payment step or schedule capture
- derived field handling where appropriate

#### Acceptance Shape

The create flow should be complete enough that an operations user can enter a new lease without falling back to the legacy system.

### Inline Customer Creation

#### Included

- create customer without leaving lease creation
- return the newly created customer into the current lease form

#### Why It Is In MVP

This directly addresses a real data entry pain point observed in the legacy flow.

### Lease List, Search, and Filter

#### Included

- lease list screen
- text search
- status filter
- search across lease number, VIN or serial, customer name, and customer code or number
- pagination or performant incremental loading

#### Why It Is In MVP

Portfolio management begins with finding the record quickly. This screen becomes the operational home base.

### Lease Detail

#### Included

- customer summary
- lease summary
- financial summary
- asset list
- future payment schedule
- derived lease metrics

#### Why It Is In MVP

Users need a read-friendly operational detail view before we expose broader editing.

### Cash Flow Generation

#### Included

- generation of lease cash flows from current schedule data
- support for remaining cash flow calculations based on future-dated rows
- treatment consistent enough to support IRR and NPV outputs

#### Why It Is In MVP

Cash flow generation is the bridge between raw schedule rows and portfolio decision support.

### IRR, NPV, and Remaining Metrics

#### Included

- IRR
- NPV
- remaining term
- remaining total or remaining future payments

#### Scope Notes

These metrics should be derived from current schedule data and lease financial context, not from stale imported summaries.

### Last Payment Date Logic

#### Included

- derive and persist last payment date based on lease timing rules
- ensure the field remains coherent when lease timing inputs change

#### Why It Is In MVP

This looks small, but it affects search, detail display, reporting, and operational trust in the lease record.

## V1 Scope

V1 extends the MVP into controlled editing and portfolio operations after lease creation.

### Lease Edit

- edit core lease information after creation
- protect fields that should not be casually mutated without recalculation or validation
- define what constitutes a structural edit versus an informational edit

### Schedule Replacement

- allow full replacement of a lease schedule when business rules require it
- replace both editable rows and any dependent derived data safely
- avoid partial updates that leave steps and actual schedule rows out of sync

### Schedule Condensing

- condense row-level schedule entries back into interpretable payment steps when possible
- preserve editability while reducing unnecessary row noise
- use this primarily as a maintenance and regeneration aid, not as the only billing representation

### Asset Edit

- update asset descriptive fields after lease creation
- support corrections without forcing lease recreation

### Asset Status Update

- mark assets active or inactive
- enforce consistent status semantics across lease detail, search, and downstream calculations

### Partial Asset Removal Logic

- support removal of one or more assets from a multi-asset lease
- log the removal event and affected values
- treat this as a lease adjustment scenario, not a silent delete

### Future Payment Reduction

- reduce future scheduled payment rows when asset removal or other approved business events change the lease economics
- apply only to future rows, not historical schedule entries

### Inactive Asset Logs

- maintain an audit trail of removed or inactivated assets
- capture the values needed to explain how lease economics changed

### Dashboard KPIs

- portfolio-level counts and totals
- active leases
- inactive leases
- key exposure or balance views
- summary metrics that support day-to-day oversight

#### Why Dashboard KPIs Are V1, Not MVP

The dashboard is valuable, but getting record-level behavior correct is more important than adding aggregated views too early.

## Later Scope

These items are intentionally deferred because they add complexity around data ingestion, reconciliation, and broader analytics.

### CSV Import Pipeline

- structured import of customers, leases, assets, financials, and schedules
- mapping validation and import staging

### Duplicate-Safe Import Behavior

- import rules that avoid silently duplicating customers, leases, or assets
- record matching rules strong enough for operational trust

### Asset ID Compatibility Helpers

- utilities that help align old asset identifiers with new canonical identifiers
- particularly useful where imported data has inconsistent VIN, serial, or generated asset ID formats

### Richer Analytics and Reporting

- portfolio analytics beyond record-level KPIs
- aging, concentration, trend, and performance views

### Verification and Reconciliation Utilities

- tooling to compare imported values against expected portfolio calculations
- utilities used during migration and ongoing data quality checks

## Scope Boundaries and Tradeoffs

### Removed From Current Scope

#### Net Cap Cost import calculation

Reasoning:

- this is a migration-time behavior with too much hidden legacy coupling
- it adds risk to the initial data pipeline and muddies domain ownership
- we can still store and review net cap cost without reproducing fragile import derivations immediately

#### Legacy schedule compatibility

Reasoning:

- compatibility logic tends to preserve old edge cases instead of clarifying the new model
- the new system needs a clean schedule contract first
- backwards accommodation can be added later as a deliberate import or migration utility, not as a core runtime rule

## Definition of Success for This Plan

The MVP is successful when a user can:

- find an existing lease by any of the key business identifiers
- create a lease with customer, financial, asset, and payment information
- add a customer inline if needed
- open a lease detail page and trust the summary, schedule, and metrics shown there

V1 is successful when a user can:

- safely edit leases and assets
- handle schedule replacement and condensation without corrupting downstream calculations
- manage asset removals with traceable financial consequences
- use dashboard KPIs for operational oversight

Later phases are successful when:

- migration and import become safer than manual cleanup
- analytics broaden without weakening operational correctness
- data verification becomes systematic rather than ad hoc
