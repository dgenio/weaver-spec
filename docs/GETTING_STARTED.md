# First success

This is the shortest supported path from clone to a real Weaver contract check.
It uses only repository fixtures and the reference conformance runner; no model,
API key, sibling runtime, or network service is required after dependencies are
installed.

> [!NOTE]
> This walkthrough demonstrates the **current reference-stack contracts**. The
> pre-1.0 adoption reset is revalidating which concepts should remain stable or
> become optional profiles. Passing this walkthrough is not evidence that the
> full current contract set will become an industry standard.

## Prerequisites

- Python 3.10 or newer
- Git

## 1. Clone and install validation dependencies

```bash
git clone https://github.com/dgenio/weaver-spec.git
cd weaver-spec
python -m venv .venv
. .venv/bin/activate
pip install -e "contracts/python[dev]"
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## 2. Run the reference implementation

```bash
python examples/reference_impl/reference_impl.py
```

This constructs the current Core artifacts through the reference happy path and
runs the assertions kept green by CI.

## 3. Validate one real external-style payload

The repository contains a signed `TraceBundle` fixture whose public test key is
part of the conformance keyring:

```bash
python conformance/run.py \
  --bundle conformance/fixtures/trace_bundle_signed_valid.json
```

Expected result: the command exits successfully after schema, invariant, and
signature checks pass.

## 4. Tamper with the payload and see the check fail

Copy the signed payload and alter the model-visible result after it was signed:

```bash
cp conformance/fixtures/trace_bundle_signed_valid.json /tmp/weaver-first-bundle.json
python - <<'PY'
import json
from pathlib import Path

path = Path("/tmp/weaver-first-bundle.json")
bundle = json.loads(path.read_text())
bundle["frames"][0]["summary"] = "Tampered after signing"
path.write_text(json.dumps(bundle, indent=2) + "\n")
PY
```

Now validate the modified payload:

```bash
python conformance/run.py --bundle /tmp/weaver-first-bundle.json
```

Expected result: the command exits non-zero because the signed artifact no longer
matches its verified contents.

That pass/fail loop is the essential contract-development workflow: use a
versioned payload, run machine-checkable validation, and make incompatibility
visible instead of relying on prose claims.

## Next steps

- [Quickstart](QUICKSTART.md) — Python and JavaScript/TypeScript integration
  patterns.
- [Adoption Guide](ADOPTION_GUIDE.md) — current reference-stack adoption modes.
- [Conformance](CONFORMANCE.md) — corpus, invariants, signatures, and downstream
  CI use.
- [Contract Reference](CONTRACT_REFERENCE.md) — current fields and tiers.
