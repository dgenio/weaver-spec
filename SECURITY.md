# Security Policy

## Supported Versions

`weaver-spec` is a documentation and contracts repository. It does not ship executable runtime code beyond the minimal `weaver_contracts` Python package used for contract validation.

| Version | Supported |
|---------|-----------|
| 0.x (current) | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in the `weaver_contracts` Python package, the JSON Schemas, or the CI workflows, please **do not open a public issue**.

Instead, report it privately:

1. Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) feature on this repository.
2. Include:
   - A description of the vulnerability and its potential impact.
   - Steps to reproduce.
   - Any suggested remediation.

We will acknowledge receipt within 3 business days and aim to publish a fix or advisory within 14 days of confirmation.

## Scope

This security policy covers:

- The `weaver_contracts` Python package (`contracts/python/`).
- CI workflow definitions (`.github/workflows/`).
- JSON Schema files that may be used in security-sensitive validation contexts.

It does **not** cover the sibling runtime repositories (`contextweaver`, `agent-kernel`, `ChainWeaver`), which maintain their own security policies.

## Security Considerations for Adopters

- The `weaver_contracts` package has **no runtime dependencies** beyond the Python standard library. This minimises supply chain risk.
- JSON Schemas should be loaded from trusted sources; do not load schemas from untrusted user input without validation.
- Contract tokens (`CapabilityToken`) contain authorization scope. Treat them with the same care as bearer tokens.
