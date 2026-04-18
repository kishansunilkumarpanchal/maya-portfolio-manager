# Maya Portfolio Manager Decision Log

## Purpose

This log records the meaningful product and architecture decisions that are shaping Maya Portfolio Manager. The intent is to preserve reasoning, not just outcomes. These entries reflect current decisions already made during planning and migration thinking.

Use this file as a living log for decisions that affect:

- product scope
- data modeling
- search behavior
- migration boundaries
- implementation sequencing

Date fields may be filled in when entries are formally adopted.

## Entry Format

- `Status`: Proposed, Accepted, Superseded, or Deferred
- `Date`: `[YYYY-MM-DD]` when finalized
- `Decision`: short statement of what was decided
- `Reasoning`: why the decision was made
- `Consequence`: what this changes for implementation

---

## D-001: Portfolio Search Must Cover Operational Identifiers

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: Global lease search must support lease number, VIN or serial, customer name, and customer code or number.
- `Reasoning`: Users do not search the portfolio from a single consistent identifier. In practice, the information available at lookup time varies by task. Designing search around only lease number or only customer name would force workarounds and reduce trust in the new system.
- `Consequence`: Search architecture, schema indexing, and API design must treat these fields as first-class search inputs. Lease list behavior cannot be implemented as a narrow single-table filter.

## D-002: Customer Suggestions Should Appear After a Few Typed Characters

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: Customer suggestions in lease creation should appear only after the user has typed a few characters, not immediately from the first keystroke.
- `Reasoning`: The goal of suggestions is to reduce duplicate customer creation and speed up lease entry. Triggering too early produces noisy result sets and a poor interaction pattern, especially in a portfolio with many similarly named customers.
- `Consequence`: The frontend should use a minimum-character threshold before querying suggestions, and the backend should optimize for partial-name and customer-code lookups in that thresholded flow.

## D-003: Keep Both `payment_steps` and `lease_payment_schedules`

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: The system will keep both `payment_steps` and `lease_payment_schedules` as separate persisted structures.
- `Reasoning`: The legacy behavior already demonstrates that a lease needs both a compact payment pattern definition and an actual row-level schedule. The row-level schedule is required for UI editing, row-specific adjustments, and calculations after edits. Collapsing the two would either make the schedule model too abstract for editing or too noisy for meaningful pattern management.
- `Consequence`: Schedule-related services must explicitly define whether they are reading or writing payment pattern data, actual schedule rows, or both. The schema and API contracts should not treat the two tables as duplicates.

## D-004: `payment_steps` Represent Recurring Pattern Definition

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: `payment_steps` are the recurring or structured payment definition for a lease.
- `Reasoning`: This table is the clean business representation of how the schedule is intended to behave over time. It is useful for initial generation, regeneration, and condensing detailed rows back into understandable step patterns.
- `Consequence`: Payment-step logic should stay compact and interpretable. It should not be stretched to encode every row-level exception created during later edits.

## D-005: `lease_payment_schedules` Represent Actual Editable Rows

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: `lease_payment_schedules` are the actual dated rows used for UI editing, row-level adjustments, and post-edit calculations.
- `Reasoning`: Real lease operations require schedule rows that may diverge from the original recurring pattern. Once edits occur, those rows become the correct operational basis for detail views, future payment calculations, and metrics.
- `Consequence`: Lease detail and edit workflows should read schedule rows as the authoritative current schedule. Metric calculations should use current schedule data rather than relying only on recurring pattern definitions.

## D-006: Remove Net Cap Cost Import Calculation from Current Scope

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: Net Cap Cost import-side calculation will not be implemented in the current scope.
- `Reasoning`: This behavior belongs to the migration and import boundary, not the core lease-management runtime. Pulling it into the first implementation would introduce legacy coupling and make the initial data model harder to clarify.
- `Consequence`: MVP implementation can still store and display net cap cost where needed, but it does not need to reproduce legacy import logic. Import calculations can be added later as a deliberate pipeline feature if they remain necessary.

## D-007: Remove Legacy Schedule Compatibility from Current Scope

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: Legacy schedule compatibility behavior is excluded from the current product scope.
- `Reasoning`: Compatibility logic tends to preserve implementation debt from the old application and obscures the clean contract needed for the new schedule model. The new system needs a stable internal definition of pattern steps and actual schedule rows before it absorbs legacy accommodation rules.
- `Consequence`: The backend and schema can be designed around the new schedule contract. Any later support for old schedule formats should be handled through migration or import utilities, not through the core runtime model.

## D-008: Inline Customer Creation Is Part of Core Workflow, Not a Nice-to-Have

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: Users must be able to create a customer inline during lease creation.
- `Reasoning`: Lease intake is already a multi-part workflow. Forcing users to leave the screen to create a missing customer would add friction and increase the chance of incomplete or duplicated entry attempts.
- `Consequence`: The frontend create flow and backend APIs should support a nested or adjacent customer-creation path that returns the new customer directly into the active lease workflow.

## D-009: Dashboard KPIs Are Important but Follow Record-Level Correctness

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: Dashboard KPIs belong in V1 rather than MVP.
- `Reasoning`: Aggregated visibility is useful, but the more important near-term risk is getting customer, lease, asset, schedule, and metric behavior correct at the record level. A dashboard built on unstable record logic would create misleading confidence.
- `Consequence`: Delivery should prioritize lease list, creation, detail, schedule behavior, and core metrics before portfolio-wide summaries.

## D-010: Asset Removal Must Preserve a Log of Financial Impact

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: Partial asset removal should create an inactive asset log and reduce future schedule impact without deleting historical meaning.
- `Reasoning`: Asset removal changes the economics of the lease. A simple delete would erase why the lease changed and make it harder to explain downstream payment reductions or residual adjustments.
- `Consequence`: V1 data modeling should retain `inactive_asset_logs` or an equivalent structure, and asset-removal services must update current state while preserving a record of the change.

## D-011: The New App Is a Domain Migration, Not a Literal Rewrite

- `Status`: Accepted
- `Date`: `[YYYY-MM-DD]`
- `Decision`: The move from Flask + SQLAlchemy to FastAPI + React + MUI + PostgreSQL is a domain-guided rebuild, not a literal port.
- `Reasoning`: The legacy app contains valuable business behavior, but it also contains route-level logic, migration-specific workarounds, and compatibility concerns that should not be copied by default. The new architecture needs to preserve intent while improving clarity and maintainability.
- `Consequence`: Planning and implementation should regularly ask whether a behavior is business-critical or simply legacy-specific. Only the former should shape the new core platform.

## How to Use This Log Going Forward

Add a new entry when a decision:

- changes scope or sequencing
- introduces or removes a data model
- affects search, schedule, or calculation behavior
- changes how migration concerns are handled

Update an existing entry when:

- implementation clarifies the original decision without changing it

Supersede an entry when:

- a later decision intentionally replaces it and the replacement should be traceable
