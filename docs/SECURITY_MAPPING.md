# Security Framework Mapping

This document maps the Weaver invariants `I-01` through `I-07` (defined in [`docs/INVARIANTS.md`](INVARIANTS.md)) to three external security frameworks:

1. [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/)
2. [MITRE ATLAS](https://atlas.mitre.org/)
3. [NIST AI Risk Management Framework 1.0](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf)

This is an **alignment** map, **not** a certification claim. Each row uses the wording "aligned with" only. `weaver-spec` is documentation and contracts — enforcement happens in the sibling runtimes. Adopters who wish to claim compliance with any of the frameworks below must perform their own conformance work in their implementation.

For the underlying invariants themselves, [`docs/INVARIANTS.md`](INVARIANTS.md) is authoritative.

---

## Alignment with OWASP LLM Top 10 (2025)

| Invariant | Aligned with | Rationale |
| ----------- | -------------- | ----------- |
| **I-01** LLM never sees raw tool output by default | [LLM02:2025 Sensitive Information Disclosure](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/), [LLM05:2025 Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/), [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm012025-prompt-injection/) | The `Frame` boundary forces every tool result through the firewall before any LLM-visible representation is produced. This is aligned with disclosure prevention (LLM02), output handling (LLM05), and indirect prompt-injection blocking when tool output is itself untrusted (LLM01). |
| **I-02** Every execution authorized and auditable | [LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) | Pairing every execution with a `PolicyDecision` and a `TraceEvent` is aligned with the LLM06 controls that require auditable authorization for any tool action an agent can invoke. |
| **I-03** Routing without full tool schema injection | [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm012025-prompt-injection/), [LLM10:2025 Unbounded Consumption](https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/) | Bounded `ChoiceCard`s reduce the attack surface that prompt injection can pivot through (LLM01) and bound per-turn token consumption (LLM10). |
| **I-04** Contracts minimal and stable | [LLM05:2025 Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/), [LLM03:2025 Supply Chain](https://genai.owasp.org/llmrisk/llm032025-supply-chain/) | A minimal Core surface reduces the number of fields any consumer must sanitize (LLM05) and makes the supply-chain promise verifiable across sibling repos (LLM03). |
| **I-05** contextweaver receives Frames, not raw output | [LLM02:2025 Sensitive Information Disclosure](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/), [LLM05:2025 Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/) | Restating I-01 at the ingestion boundary; aligned with the same disclosure and output-handling categories. |
| **I-06** CapabilityTokens are single-use or scoped | [LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) | Scope-bounded, time-bounded, or single-use tokens are the canonical LLM06 mitigation for limiting agent authority. |
| **I-07** ChainWeaver delegates execution to the kernel | [LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) | Routing every tool invocation through the authorized execution layer is aligned with LLM06's "minimum-privilege execution path" principle. |

---

## Alignment with MITRE ATLAS

ATLAS technique URLs follow the pattern `https://atlas.mitre.org/techniques/<technique-id>`.

| Invariant | Aligned with | Rationale |
| ----------- | -------------- | ----------- |
| **I-01** LLM never sees raw tool output by default | [AML.T0051 LLM Prompt Injection](https://atlas.mitre.org/techniques/AML.T0051/) (indirect variant) | Filtering raw tool output through the firewall before LLM consumption is aligned with mitigations for indirect prompt injection delivered through untrusted tool results. |
| **I-02** Every execution authorized and auditable | [AML.T0040 AI Model Inference API Access](https://atlas.mitre.org/techniques/AML.T0040/) | Authorized-and-audited execution is aligned with the detection and response controls that bound and log inference-API access. |
| **I-03** Routing without full tool schema injection | [AML.T0051 LLM Prompt Injection](https://atlas.mitre.org/techniques/AML.T0051/) | A smaller per-turn context surface is aligned with reducing the prompt-injection attack surface. |
| **I-04** Contracts minimal and stable | [AML.T0051 LLM Prompt Injection](https://atlas.mitre.org/techniques/AML.T0051/) | Stable, minimal contracts reduce the number of structurally-distinct inputs an adversary can manipulate downstream. |
| **I-05** contextweaver receives Frames, not raw output | [AML.T0051 LLM Prompt Injection](https://atlas.mitre.org/techniques/AML.T0051/) (indirect variant) | Restating I-01 at the ingestion boundary. |
| **I-06** CapabilityTokens are single-use or scoped | [AML.T0024 Exfiltration via AI Inference API](https://atlas.mitre.org/techniques/AML.T0024/), [AML.T0040 AI Model Inference API Access](https://atlas.mitre.org/techniques/AML.T0040/) | Scoped, time-bounded tokens are aligned with mitigations that limit blast radius once an inference API is reached. |
| **I-07** ChainWeaver delegates execution to the kernel | [AML.T0040 AI Model Inference API Access](https://atlas.mitre.org/techniques/AML.T0040/) | Funnelling all tool invocations through one authorized path is aligned with bounding the inference-API access surface. |

---

## Alignment with NIST AI RMF 1.0

The [NIST AI RMF 1.0](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf) defines four core functions: **Govern**, **Map**, **Measure**, and **Manage**.

| Invariant | Aligned with function | Rationale |
| ----------- | ----------------------- | ----------- |
| **I-01** LLM never sees raw tool output by default | Manage | A persistent firewall control aligned with the Manage function's risk-response responsibilities for in-production AI systems. |
| **I-02** Every execution authorized and auditable | Govern, Measure | Authorization policies are aligned with Govern; the auditable `TraceEvent` log is aligned with Measure (monitoring and assessment). |
| **I-03** Routing without full tool schema injection | Map | Bounding the prompt surface is aligned with Map (context and risk identification for the specific AI system). |
| **I-04** Contracts minimal and stable | Govern | Minimal, stable interface surfaces are aligned with the Govern function's policy and accountability responsibilities. |
| **I-05** contextweaver receives Frames, not raw output | Manage | Restating I-01 at the ingestion boundary. |
| **I-06** CapabilityTokens are single-use or scoped | Govern, Manage | Scope and lifetime policies are aligned with Govern; per-execution issuance and revocation are aligned with Manage. |
| **I-07** ChainWeaver delegates execution to the kernel | Govern | A single authorized execution path is aligned with Govern's accountability and oversight role. |

---

## Wording rule

This document uses **"aligned with"** exclusively. The Weaver spec does not certify any implementation against any framework, and no implementation should claim compliance with a framework based on this alignment table alone.

See [AGENTS.md](../AGENTS.md) "Forbidden behaviors" for the underlying rule against aspirational language in this repository.

---

## Update triggers

Update this file when:

- A new invariant is added to [`docs/INVARIANTS.md`](INVARIANTS.md).
- Any of the three external frameworks publishes a new major version (OWASP LLM Top 10, MITRE ATLAS, NIST AI RMF).
- A row's rationale becomes outdated because a Core contract changed.
