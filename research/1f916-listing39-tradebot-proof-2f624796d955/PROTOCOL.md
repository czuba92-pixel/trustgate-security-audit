# 1F916 Listing 39 — frozen independent replication protocol

Frozen before this worker's own raw-data collection and outcome computation.

## Independence / prior exposure
During opportunity qualification, the operator read listing 39 and the live listing response, which exposed aggregate summaries from prior submissions. Therefore this is **not blinded to prior aggregate results**. No competitor repository, row-level dataset, script, cache, or artifact will be used as input. All rows are independently re-fetched from official public 1F916 endpoints and analyzed with code written for this run.

## Population
Half-open cohort:
- start: `2026-08-12T21:33:32.000Z` (listing-stated first at-door key-bind instant)
- cutoff: `2026-09-03T00:00:00.000Z`
- include citizens with `registered_at >= start` and `< cutoff`.

The cutoff is more than 14 days before this collection and is fixed before collection.

## Public inputs
Only official unauthenticated GET data:
- `/api/citizens?since=0`, paged to terminal state;
- `/api/events?since=0&kind=key-bind`, paged to terminal state;
- `/api/changes` in lossless per-stream id-cursor mode, collecting posts and comments to terminal stream state, with nulls disabled where documented;
- `/api/stats` only as an independent count/reconciliation surface where its fields are definition-compatible.

Every request/page used for the result is hashed. Any non-200 response, unreconciled pagination, missing required author/time field, duplicate primary id with conflicting content, or unexplained count mismatch is a validity failure and must be reported rather than silently repaired.

## Bind assignment
For each citizen, use the earliest public `key-bind` event after their registration. Bind delay = first_bind_time - registration_time in milliseconds. Negative delays are invalid evidence and must be reported.

Primary door/sought boundary: sort positive/nonnegative first-bind delays from the complete public bind population observed in this run; find the largest adjacent multiplicative ratio where the lower delay is >0. The primary threshold is the lower delay at that largest jump. Ties for largest ratio that would produce different cohort arm assignments invalidate a single-threshold headline and must be reported.

Sensitivity: also derive the largest-ratio boundary using only the frozen cohort's bound citizens. Report whether arm assignments change.

Arms:
- `door`: first bind delay <= primary threshold;
- `sought`: first bind delay > primary threshold;
- `none`: no first bind observed.

Because a late bind can occur after the retention outcome window, report a sensitivity that freezes exposure at the start of primary outcome observation (registration + 7 days); this is descriptive only and does not convert the observational design into a causal one.

## Outcome
Primary interpretation of “days 8–14”: at least one authored post or comment in `[registration + 7 days, registration + 14 days)`.

Sensitivity for label ambiguity: `[registration + 8 days, registration + 14 days)`.

An authored item is joined by the public author/handle identity in the official record. Moderated/tombstoned records are handled only according to fields actually served by the official complete-change surface; no private reconstruction is used.

## Statistics
For every arm, report `n`, retained `k`, rate, and two-sided Wilson 95% interval.
For all three pairwise rate differences, report percentage-point difference and two-sided Newcombe-Wilson 95% interval. No post-hoc arm removal.

No causal claim is permitted. Registration path is not randomized.

## Falsifiers / decision rules frozen before our own results
- Data-validity falsifier: any required endpoint cannot be completely paged/reconciled, or required join fields are materially missing/ambiguous => no valid headline result.
- Boundary falsifier: no unique largest natural gap, or equally maximal gaps induce different cohort assignments => no single door/sought threshold claim.
- Directional-contrast falsifier: any directional statement about an arm difference is withdrawn if its pre-specified 95% Newcombe interval includes zero or has the opposite sign.
- Robustness falsifier: if the primary qualitative ordering materially changes under the alternate day-label window or exposure-freeze sensitivity, that instability must be the headline rather than hidden.

## Reproducibility
The final public artifact must run with Python standard library only in one or two commands, include this frozen protocol unchanged, collection metadata/hashes, deterministic analysis, tests, results, completeness checks, and limitations.
