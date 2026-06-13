# weaver-stack (umbrella meta-package)

`weaver-stack` lets you adopt a known-compatible slice of the [Weaver
Stack](https://github.com/dgenio/weaver-spec) in one line. It ships **no code** —
it only pins a compatible set of the stack's packages.

```bash
pip install weaver-stack            # the spec contracts (weaver_contracts)
pip install weaver-stack[runtime]   # + the runtime siblings (once verified)
```

## Convenience, not coupling

The meta-package is a convenience for adopters who want "the whole compatible
set" without hand-resolving versions. It is **not** a coupling:

- Every member of the stack remains independently installable and usable on its
  own (`pip install weaver_contracts`, etc.).
- You can ignore the meta-package entirely and read the JSON Schemas directly.
- Installing `weaver-stack` never pulls in more than the extras you ask for; the
  base install is just `weaver_contracts`.

## What gets pinned

| Extra      | Members                                                   |
| ---------- | --------------------------------------------------------- |
| *(base)*   | `weaver_contracts` (the canonical spec contracts)         |
| `runtime`  | The request-path siblings: contextweaver → agent-kernel → ChainWeaver |
| `devtools` | Spec-authoring / developer tooling                        |

The pinned versions are the **executable form of the compatibility promise** in
[`compatibility.yaml`](../../compatibility.yaml). A sibling is added to the
`runtime` extra only once it is marked `verified` or `provisional` with a
`tested_version` there; `scripts/validate_meta_package.py` (the
`validate-meta-package` CI job) fails the build if the pins and the manifest
disagree. This is deliberate: the meta-package can only ever resolve to versions
the spec has actually vouched for — never an aspirational pin.

> [!NOTE]
> The `runtime` extra is currently empty: the siblings are still `unverified` in
> `compatibility.yaml`. The base install (`weaver_contracts`) is fully
> functional today; `runtime` populates automatically as siblings are verified.

## Versioning

This meta-package's MINOR tracks the `weaver_contracts` / contract MINOR it
certifies (currently `0.7.x`).
