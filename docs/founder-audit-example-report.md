# TrustGate Founder Audit — example deliverable format

**Illustrative report structure only.** This is not an actual customer audit, penetration test, certification, or claim that any named system passed or failed. The actual findings depend on a separately authorized, agreed target and test run.

## 1. Engagement boundary
- Target name and version/commit: **[agreed target]**
- Test environment: **[isolated / staging only]**
- Explicit authorization and restrictions: **[documented permission and stop conditions]**
- Included: one agreed MCP or agent-commerce authorization/payment workflow.
- Excluded by default: production purchases, private keys, customer data, smart-contract reviews, infrastructure penetration testing, legal or regulatory certification.

## 2. Checks and expected negative controls

| Control | Representative question | Evidence the customer receives |
| --- | --- | --- |
| Authorization/context binding | Does a permission still apply after a relevant target/action parameter changes? | Allowed/denied outcome, bounded inputs, reason |
| Replay resistance | Can an old or previously used approval be reused? | Test sequence, observed refusal or deviation |
| Idempotency | Can retrying the same request unexpectedly repeat a side effect? | Stable request identity and repeat outcome |
| Fail-closed handling | What happens if required state or context is missing or invalid? | Refusal path and reproducible evidence |

## 3. Example finding entry (template)

**Finding ID:** TG-001

**Category:** [authorization binding / replay / idempotency / fail-closed]

**Verdict:** [PASS / FAIL_CLOSED / FAIL / INCONCLUSIVE]

**Expected behavior:** [agreed security property]

**Observed behavior:** [the actual result of the scoped run]

**Safe reproduction:** [minimal authorized commands or test steps with secrets redacted]

**Evidence:** [relevant non-sensitive response fields, timestamps, versions, hashes or screenshots as appropriate]

**Impact and limits:** [what the result proves, and what it does not]

**Suggested correction:** [a scoped next action, only if a defect is observed]

## 4. Summary and handoff
- Findings by severity, with no invented scores.
- Controls covered and controls **not** tested.
- Retest suggestions for any observed defect.
- Concise signed-off scope summary and reproducibility notes.

**Purchase/engagement terms:** The Founder Audit is **US$49 for one explicitly authorized target**. We confirm fit and permission before testing. A clean result is not a guarantee of vulnerability-free software or a full independent security certification.

[View the offer and request a free scope check](https://czuba92-pixel.github.io/trustgate-security-audit/).
