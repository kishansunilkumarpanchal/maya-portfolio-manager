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

- `Date`: `[YYYY-MM-DD]` when finalized
- `Phase`: Phase #
- `Context`: Brief context of what was decided
- `Decision`: Explanation of what was decided
- `Why`: why the decision was made
- `Impact`: what this changes for implementation

---

## Decision #001 - Lease Search Scope

**Date:** 2026-04-18  
**Phase:** Phase 2 - Planning  
**Context:** Expanding lease search beyond legacy app  

**Decision:**
Search will support:
- Lease Number (partial)
- VIN / Serial Number (partial)
- Customer Name (partial with suggestions)
- Customer Code/Number

**Why:**
- Real-world users often search by VIN
- Customer-based lookup is common in operations
- Improves usability vs legacy system

**Impact:**
- Requires indexing on leases, customers, and assets
- Affects API design and query structure



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
