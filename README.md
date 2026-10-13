# TrustGate — Dynamic MCP & Agent-Commerce Security Audit

**Find authorization and payment-flow weaknesses before deployment.**

TrustGate is an independent security-audit service for teams building MCP servers, AI-agent purchasing flows, and agent-commerce integrations.

**Founder Audit: US$49, one-time, for one authorized target.**

- [See the audit offer and scope](https://czuba92-pixel.github.io/trustgate-security-audit/)
- [Buy the Founder Audit securely on Stripe](https://buy.stripe.com/6oU9AU8C6ahTcoY75A8ww00)

## What we test

For a target you own or are explicitly authorized to test:

- **Authorization binding** — does the approved action remain bound to its actual context?
- **Replay resistance** — are stale or reused authorizations rejected?
- **Idempotency** — can repeated requests have unintended effects?
- **Fail-closed behavior** — what happens when state, permissions, or request context is invalid?

## Deliverables

A concise findings report for the agreed target, with observed PASS / FAIL_CLOSED behavior, reproduction notes, and the security impact of any identified issues.

Testing begins only after target details and proof of authorization are agreed. This is a narrowly scoped dynamic assessment, **not** a guarantee of vulnerability-free software, a full penetration test, or an automatic live-payment execution service.

## Current validation evidence

TrustGate v0.5 has passed 30/30 local unit and integration tests. Its safe reference MCP target passed 15/15 scanner cases; deliberately vulnerable replay and idempotency fixtures were rejected by the expected controls.

These results evaluate the **test harness**, not a customer's infrastructure.

## Buy or contact

**[Founder Audit — US$49 on Stripe](https://buy.stripe.com/6oU9AU8C6ahTcoY75A8ww00)**

Questions or authorization-scoping enquiries: [czuba92@gmail.com](mailto:czuba92@gmail.com)

Operated independently in Poland. Only explicitly authorized targets are tested.
