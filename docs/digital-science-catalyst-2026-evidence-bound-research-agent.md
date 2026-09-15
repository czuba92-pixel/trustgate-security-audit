# Evidence-Bound Research Agent — Digital Science Catalyst Grant 2026

## 1. THE PROBLEM

Research institutions are moving from AI that answers questions to AI that performs multi-step research work. For a research-office analyst, evidence-synthesis team, funder or R&D decision maker, the difficult question is no longer only “is the answer useful?” It is “can I reconstruct what the agent was asked to do, which evidence it relied on, what it excluded, where uncertainty remained, and why it stopped, escalated or recommended review?”

Today those controls are often fragmented across prompts, spreadsheets, reference managers, chat histories and manual review. That creates reviewer overhead, weak reproducibility, hidden specification drift and the risk that an unsupported or stale model output becomes a decision input. The problem recurs whenever an agent searches, screens, extracts, synthesizes and hands a result to a human decision maker.

**Evidence-Bound Research Agent** is a governance and provenance control plane for those workflows. It does not try to replace literature databases or specialist research agents. It makes a multi-tool research run bounded, auditable, recoverable and capable of refusing when evidence is insufficient.

Primary outcome metrics for a pilot would be reviewer time per completed decision packet, claim-level provenance coverage, unsupported-claim rate, and the proportion of deliberately injected specification-drift or missing-evidence cases that are caught before human sign-off.

## 2. YOUR WORKFLOW

A user starts by naming the research decision, scope, inclusion/exclusion rules, required evidence classes, stop conditions and points where human approval is mandatory. The system records this as a preregistered task envelope before retrieval begins.

The agent then:

1. freezes the task specification and creates a content-addressed run identity;
2. queries approved research/search tools and records source identity, retrieval time and lineage;
3. builds a claim-evidence ledger rather than only prose;
4. labels material statements as verified, derived, assumed or unknown;
5. checks contradictions, missing evidence, stale sources and scope drift deterministically where possible;
6. sends bounded claims requiring judgement to an independent semantic verifier;
7. refuses, flags or escalates when evidence is insufficient or a declared authority boundary is crossed; and
8. produces a decision packet containing the answer, evidence map, unresolved conflicts, verifier result, audit trail and reproduction metadata.

Humans remain accountable for high-stakes decisions. They may approve, reject, or override with an attributable reason. The funded pilot would embed this control layer around an existing research-source workflow rather than invent another literature corpus. We would prefer to integrate with Digital Science tooling such as Dimensions or ReadCube if appropriate access and product fit are available; otherwise the interface remains provider-agnostic through APIs/MCP-style connectors and exports into the institution’s existing review/reporting workflow.

## 3. TRUST, AUDIT AND GOVERNANCE

The design is grounded in a working domain prototype developed inside the Tradebot R&D project. The current prototype already implements reusable controls: crash-safe `IN_PROGRESS` / `COMPLETE` task state with an exact recovery step; a SHA-256 chained journal whose previous-event hash is verified; binding of stored context to live repository state so stale memory cannot silently become current truth; explicit authority flags; fail-closed handling of missing or ambiguous evidence; separation of builder and independent semantic-verifier roles for high-risk decisions; and source/evidence references retained with checkpoints rather than only in a final narrative.

These mechanisms are implemented today for financial-market R&D. They are **not yet a general research product**, and Tradebot’s autonomous Brain is not being represented here as a deployed institutional research agent. The grant would fund extraction of the generic control plane and validation in a bounded research-lifecycle use case.

A user would see both result and process: source manifest, claim-to-source mapping, checks, verifier verdict, unknowns and intervention points. `UNKNOWN`, refusal and escalation are valid terminal states. Human overrides remain attributable. The goal is not to claim that AI cannot fail; it is to make failure, uncertainty and scope changes visible before they silently propagate into a consequential decision.

## 4. TEAM

This is currently a solo founder/operator project developed through sustained AI-assisted engineering and verifier-driven iteration. The underlying control architecture has been built and stress-tested over roughly six months as part of a real discovery-system project rather than created for this grant application. The strongest existing experience is in autonomous workflow design, evidence discipline, fail-closed control, adversarial verification, machine-readable audit trails and recovery from interrupted agent work.

I do not claim academic-domain expertise that I do not have. A funded phase would therefore include a research-office or evidence-synthesis pilot partner and structured domain review as a requirement. Digital Science’s research-software experience is one reason this grant is unusually well matched to the project’s next step.

## 5. WHERE YOU ARE TODAY

Stage: **working domain prototype; research-workflow product not yet extracted**.

The prototype exists on a live VPS as a governed R&D system with canonical hash-chained project memory, preregistered task patterns, evidence references, independent-verifier routing, explicit authority boundaries and fail-closed recovery after interrupted runs. Separately, Tradebot exposes public machine-to-machine x402 services, including a market-data integrity attestation and a pre-trade execution-risk gate, demonstrating that deterministic decision services can be packaged behind machine-payable APIs.

Public service base: https://api.tradebot.devs.surf

The proposed research product has **no research users or customers today**, and Tradebot currently has **zero verified external customer sales**. That is intentionally disclosed. What has been tested is the control architecture itself: repeated negative cases, recovery paths, verifier separation, authority boundaries and live-state binding. The next evidence we need is whether those controls improve a real research workflow rather than only our original finance-domain workflow.

## 6. ALTERNATIVES AND COMPETITORS

Doing nothing means relying on manual review, prompt histories and each application’s local audit features. Strong research products already solve important adjacent problems. Elicit (https://elicit.com/) provides systematic-review workflows with auditable screening and source-backed extraction. Scite (https://scite.ai/) provides citation-context intelligence and source-grounded research assistance. Undermind (https://www.undermind.ai/) performs deep literature search with traceable citations. Digital Science itself is advancing agentic research analytics through its research-data and workflow products.

We should not copy those products. Evidence-Bound Research Agent is intended as a **control layer across heterogeneous tools**. Its unit of value is not “find better papers,” but “make the complete multi-step research decision process inspectable, bounded, recoverable and independently checkable.” The differentiators we would test are preregistered intent, explicit authority boundaries, tamper-evident state transitions, claim/evidence separation, independent verification and fail-closed escalation across a workflow that may use several specialist tools.

## 7. WHERE THIS GOES

The longer-term product is an institutional control plane for research agents, internal R&D copilots and funding/strategy workflows. An institution could require every consequential agentic evidence synthesis to produce a standard evidence-bound decision packet before its output enters a funding memo, review, policy recommendation or R&D decision.

Likely commercial buyers are research institutions, funders, publishers and regulated R&D teams already paying for research software but needing stronger governance for autonomous workflows. Pricing would be tested as institutional SaaS/API based on governed runs, integrations and audit retention rather than token usage alone.

The product succeeds only if it reduces human review burden **and** catches consequential uncertainty or drift earlier. If it adds ceremony without measurable decision value, the pilot should reject the direction.

## 8. FIT WITH DIGITAL SCIENCE

The initial lifecycle position is **evidence synthesis, research integrity and institutional decision support**. Digital Science is a strong partner because its products already live inside research workflows and because the 2026 Catalyst brief explicitly asks for multi-step agents with provenance, governance and accountability.

We need domain feedback on what an institution would actually accept as sufficient provenance, which interventions should require human approval, and how a control layer should integrate without duplicating existing products. Digital Science can provide exactly that product and workflow perspective. The project contributes an execution-oriented governance architecture developed under repeated adversarial testing, with refusal, uncertainty and recovery treated as first-class outputs rather than added after generation.

## 9. BUDGET

£25,000 requested: £7,000 to extract the provider-agnostic control plane; £5,000 for one research-source connector and institutional export; £4,000 for adversarial evaluation and refusal/escalation cases; £4,000 for a research-office/evidence-synthesis pilot and outcome measurement; £3,000 for privacy, security and audit-retention hardening; £2,000 for hosted prototype and reproducible demo infrastructure. The grant converts an existing finance-domain governance prototype into a validated research-domain product.
