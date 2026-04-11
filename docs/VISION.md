# Vision

## The Problem

Modern LLM-based agents face four compounding problems:

1. **Tool explosion.** A production agent may have access to 1000+ tools. Injecting all tool schemas into every prompt is expensive, noisy, and limits the effective reasoning window.
2. **Context bloat.** Raw tool outputs—database rows, API responses, file contents—can be large, sensitive, and unsafe to pass directly to an LLM without filtering or summarisation.
3. **Unsafe execution.** Without a principled authorization layer, an agent can call any tool with any arguments. There is no auditable record of what ran, why, and on whose authority.
4. **Flaky multi-step orchestration.** Ad-hoc chaining of LLM calls and tool calls produces non-deterministic, hard-to-debug pipelines. Retries, partial failures, and state management are solved differently in every implementation.

## What "Good" Looks Like

A well-designed agent ecosystem satisfies four properties:

| Property | Definition |
| ---------- | ----------- |
| **Bounded choices** | The LLM selects from a small, curated set of pre-screened options, not from an unbounded tool list. |
| **Auditable execution** | Every tool invocation is authorized, recorded, and attributable to a specific request and principal. |
| **Safe outputs** | The LLM never sees raw tool output by default. Outputs are firewalled, summarised, or redacted before entering the context. |
| **Composability** | Each component (router, kernel, flow engine) can be adopted independently and replaced without rewriting the others. |

## This Repository's Role

`weaver-spec` does not implement any of these properties. It defines the **contracts, vocabulary, and invariants** that make it possible for independent implementations to satisfy them together. It answers:

- What does a routing decision look like?
- Where does the firewall boundary sit?
- How does a capability token flow from authorization to execution?
- What is a Frame, and why does contextweaver never see raw output?

The spec is the stable foundation. The three Weaver repositories are implementations on top of it.
