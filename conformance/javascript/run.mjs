#!/usr/bin/env node
/**
 * JavaScript reference implementation of the Weaver static conformance corpus.
 *
 * This is deliberately independent code over the same normative inputs used by
 * conformance/run.py: JSON Schemas, corpus.yaml, invariants.yaml, signed fixture,
 * and test keyring. It is build-time verification only and is not published as
 * an adopter runtime package.
 */

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import canonicalize from "canonicalize";
import YAML from "yaml";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(HERE, "../..");
const CORE_SCHEMA_DIR = path.join(REPO_ROOT, "contracts/json");
const EXTENDED_SCHEMA_DIR = path.join(CORE_SCHEMA_DIR, "extended");
const CORPUS_PATH = path.join(REPO_ROOT, "conformance/corpus.yaml");
const INVARIANTS_PATH = path.join(REPO_ROOT, "conformance/invariants.yaml");
const KEYRING_PATH = path.join(REPO_ROOT, "conformance/keyring/test_keyring.json");

const FORBIDDEN_FRAME_KEYS = new Set(["raw_output", "raw", "raw_result", "tool_output"]);
const SIGNATURE_ALGS = new Set(["ed25519", "es256"]);
const STATIC_INVARIANT_IDS = new Set(["I-01", "I-02", "I-04", "I-06"]);
const ED25519_SPKI_PREFIX = Buffer.from("302a300506032b6570032100", "hex");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function readYaml(filePath) {
  return YAML.parse(fs.readFileSync(filePath, "utf8"));
}

function schemaFiles(directory) {
  return fs
    .readdirSync(directory, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".schema.json"))
    .map((entry) => path.join(directory, entry.name))
    .sort();
}

function loadSchemas() {
  const schemas = new Map();
  const ajv = new Ajv2020({
    allErrors: true,
    strict: false,
    allowUnionTypes: true,
    validateFormats: true,
  });
  addFormats(ajv);

  for (const filePath of [...schemaFiles(CORE_SCHEMA_DIR), ...schemaFiles(EXTENDED_SCHEMA_DIR)]) {
    const schema = readJson(filePath);
    const stem = path.basename(filePath).replace(/\.schema\.json$/, "");
    schemas.set(stem, schema);
    if (schema.$id) {
      ajv.addSchema(schema, schema.$id);
    } else {
      ajv.addSchema(schema, stem);
    }
  }
  return { schemas, ajv };
}

function validatePayload(ajv, schema) {
  const validator = schema.$id ? ajv.getSchema(schema.$id) : ajv.compile(schema);
  if (!validator) {
    throw new Error(`No validator compiled for schema ${schema.$id ?? schema.title ?? "<unknown>"}`);
  }
  return validator;
}

function errorMatchesDeclaredReason(violates, errors) {
  const separator = violates.indexOf(":");
  const keyword = separator === -1 ? violates : violates.slice(0, separator);
  const target = separator === -1 ? "" : violates.slice(separator + 1);
  const labelOnly = new Set(["anyOf", "oneOf", "allOf", "not"]);

  return (errors ?? []).some((error) => {
    if (error.keyword !== keyword) return false;
    if (!target || labelOnly.has(keyword)) return true;
    const haystack = `${error.instancePath ?? ""} ${error.message ?? ""} ${JSON.stringify(error.params ?? {})}`;
    return haystack.includes(target);
  });
}

function framesHaveNoRawOutput(bundle) {
  const violations = [];
  for (const [index, frame] of (bundle.frames ?? []).entries()) {
    const present = Object.keys(frame).filter((key) => FORBIDDEN_FRAME_KEYS.has(key)).sort();
    if (present.length) {
      violations.push(
        `Frame '${frame.frame_id ?? `index ${index}`}' carries forbidden raw-output key(s): ${JSON.stringify(present)}`,
      );
    }
  }
  return violations;
}

function policyDecisionsAreTraced(bundle) {
  const traced = new Set(
    (bundle.trace_events ?? [])
      .map((event) => event.decision_id)
      .filter((value) => value !== undefined && value !== null),
  );
  const violations = [];
  for (const decision of bundle.policy_decisions ?? []) {
    if (!traced.has(decision.decision_id)) {
      violations.push(`PolicyDecision '${decision.decision_id}' has no matching TraceEvent`);
    }
  }
  return violations;
}

function capabilityTokenScoped(token) {
  const violations = [];
  if (!Array.isArray(token.scope) || token.scope.length === 0) {
    violations.push("scope is empty or missing; unbounded scope is not permitted");
  }
  if (!(token.single_use === true || token.expires_at)) {
    violations.push("token is neither single_use nor has expires_at");
  }
  return violations;
}

function coreRequiredSurfaceStable(baseline, schemas) {
  const violations = [];
  for (const [stem, expected] of Object.entries(baseline)) {
    const schema = schemas.get(stem);
    if (!schema) {
      violations.push(`Core schema '${stem}' not found`);
      continue;
    }
    const actual = [...(schema.required ?? [])].sort();
    const wanted = [...expected].sort();
    if (JSON.stringify(actual) !== JSON.stringify(wanted)) {
      violations.push(`${stem}: required surface drifted — expected ${JSON.stringify(wanted)}, found ${JSON.stringify(actual)}`);
    }
  }
  return violations;
}

const BUNDLE_INVARIANTS = new Map([
  ["I-01", framesHaveNoRawOutput],
  ["I-02", policyDecisionsAreTraced],
]);

function loadInvariantRegistry() {
  const manifest = readYaml(INVARIANTS_PATH);
  const entries = manifest.invariants ?? [];
  const manifestIds = new Set(entries.map((entry) => entry.id));
  const missing = [...manifestIds].filter((id) => !STATIC_INVARIANT_IDS.has(id));
  const stale = [...STATIC_INVARIANT_IDS].filter((id) => !manifestIds.has(id));
  if (missing.length || stale.length) {
    throw new Error(
      `JavaScript invariant coverage is out of sync; missing ${JSON.stringify(missing)}, stale ${JSON.stringify(stale)}`,
    );
  }
  return new Map(entries.map((entry) => [entry.id, entry]));
}

function loadKeyring() {
  const keyring = readJson(KEYRING_PATH);
  return new Map((keyring.keys ?? []).map((entry) => [entry.kid, entry]));
}

function verifyTraceBundleIntegrity(bundle, keyring) {
  const signature = bundle.signature;
  if (!signature) return [];
  const violations = [];

  if (!SIGNATURE_ALGS.has(signature.alg)) {
    return [`unknown signature algorithm: ${signature.alg}`];
  }
  if (signature.canonicalization !== "JCS") {
    return [`unsupported signature canonicalization: ${signature.canonicalization}`];
  }
  if (!signature.kid) {
    return ["signature is missing kid"];
  }

  const key = keyring.get(signature.kid);
  if (!key) {
    // Match the Python conformance-report semantics: an unknown key means
    // cryptographic verification was not performed, never that it was trusted.
    return violations;
  }
  if (key.alg !== signature.alg) {
    return [`key ${signature.kid} algorithm ${key.alg} does not match signature ${signature.alg}`];
  }

  const payload = structuredClone(bundle);
  delete payload.signature;
  const canonical = canonicalize(payload);
  if (typeof canonical !== "string") {
    return ["JCS canonicalization failed"];
  }

  let verified = false;
  try {
    const signatureBytes = Buffer.from(signature.sig, "base64url");
    if (signature.alg === "ed25519") {
      const rawPublicKey = Buffer.from(key.public_key_b64url, "base64url");
      if (rawPublicKey.length !== 32) {
        return [`ed25519 key ${signature.kid} must be 32 bytes`];
      }
      const publicKey = crypto.createPublicKey({
        key: Buffer.concat([ED25519_SPKI_PREFIX, rawPublicKey]),
        format: "der",
        type: "spki",
      });
      verified = crypto.verify(null, Buffer.from(canonical, "utf8"), publicKey, signatureBytes);
    } else if (signature.alg === "es256") {
      // The shared test keyring currently contains no ES256 key. Keep the
      // algorithm path explicit; a future ES256 key fixture must provide a PEM,
      // DER SPKI, or JWK representation rather than inventing key encoding here.
      if (!key.public_key_pem) {
        return [`ES256 key ${signature.kid} has no public_key_pem for JavaScript verification`];
      }
      verified = crypto.verify(
        "sha256",
        Buffer.from(canonical, "utf8"),
        { key: key.public_key_pem, dsaEncoding: "ieee-p1363" },
        signatureBytes,
      );
    }
  } catch (error) {
    return [`signature verification error: ${error.message}`];
  }

  if (!verified) {
    violations.push(`signature verification failed for kid ${signature.kid}`);
  }
  return violations;
}

function relativePayload(caseEntry) {
  return readJson(path.join(REPO_ROOT, caseEntry.payload));
}

function run() {
  const { schemas, ajv } = loadSchemas();
  const corpus = readYaml(CORPUS_PATH);
  const invariants = loadInvariantRegistry();
  const keyring = loadKeyring();
  const failures = [];
  let checks = 0;

  const i04 = invariants.get("I-04");
  if (!i04?.baseline) {
    failures.push("I-04 invariant baseline missing from conformance/invariants.yaml");
  } else {
    checks += 1;
    for (const violation of coreRequiredSurfaceStable(i04.baseline, schemas)) {
      failures.push(`I-04: ${violation}`);
    }
  }

  for (const caseEntry of corpus.positive ?? []) {
    const schema = schemas.get(caseEntry.schema);
    if (!schema) {
      failures.push(`positive ${caseEntry.payload}: unknown schema ${caseEntry.schema}`);
      continue;
    }
    const payload = relativePayload(caseEntry);
    const validator = validatePayload(ajv, schema);
    checks += 1;
    if (!validator(payload)) {
      failures.push(
        `positive ${caseEntry.payload} failed ${caseEntry.schema}: ${JSON.stringify(validator.errors)}`,
      );
      continue;
    }

    if (caseEntry.schema === "capability_token") {
      checks += 1;
      for (const violation of capabilityTokenScoped(payload)) {
        failures.push(`I-06 ${caseEntry.payload}: ${violation}`);
      }
    }
    if (caseEntry.schema === "trace_bundle") {
      for (const [id, check] of BUNDLE_INVARIANTS) {
        checks += 1;
        for (const violation of check(payload)) {
          failures.push(`${id} ${caseEntry.payload}: ${violation}`);
        }
      }
      checks += 1;
      for (const violation of verifyTraceBundleIntegrity(payload, keyring)) {
        failures.push(`signature ${caseEntry.payload}: ${violation}`);
      }
    }
  }

  for (const caseEntry of corpus.negative ?? []) {
    const schema = schemas.get(caseEntry.schema);
    if (!schema) {
      failures.push(`negative ${caseEntry.payload}: unknown schema ${caseEntry.schema}`);
      continue;
    }
    const payload = relativePayload(caseEntry);
    const validator = validatePayload(ajv, schema);
    const valid = validator(payload);
    checks += 1;

    if (caseEntry.by === "schema") {
      if (valid) {
        failures.push(`negative ${caseEntry.payload} was unexpectedly schema-valid`);
      } else if (!errorMatchesDeclaredReason(caseEntry.violates, validator.errors)) {
        failures.push(
          `negative ${caseEntry.payload} failed schema for the wrong reason; expected ${caseEntry.violates}, got ${JSON.stringify(validator.errors)}`,
        );
      }
      continue;
    }

    if (caseEntry.by === "invariant") {
      if (!valid) {
        failures.push(
          `invariant-negative ${caseEntry.payload} must be schema-valid first: ${JSON.stringify(validator.errors)}`,
        );
        continue;
      }
      const check = BUNDLE_INVARIANTS.get(caseEntry.violates);
      if (!check) {
        failures.push(`negative ${caseEntry.payload}: unsupported invariant ${caseEntry.violates}`);
        continue;
      }
      checks += 1;
      if (check(payload).length === 0) {
        failures.push(`negative ${caseEntry.payload} did not violate ${caseEntry.violates}`);
      }
      continue;
    }

    failures.push(`negative ${caseEntry.payload}: unknown rejection mode ${caseEntry.by}`);
  }

  if (failures.length) {
    console.error(`JavaScript conformance FAILED: ${failures.length} failure(s), ${checks} checks`);
    for (const failure of failures) console.error(`- ${failure}`);
    return 1;
  }

  console.log(`JavaScript conformance PASS: ${checks} checks`);
  return 0;
}

process.exitCode = run();
