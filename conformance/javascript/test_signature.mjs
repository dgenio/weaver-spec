import assert from "node:assert/strict";
import crypto from "node:crypto";
import test from "node:test";

import canonicalize from "canonicalize";

import { verifyTraceBundleIntegrity } from "./run.mjs";

function signedFixture(pointFormat = "uncompressed") {
  const { privateKey, publicKey } = crypto.generateKeyPairSync("ec", {
    namedCurve: "prime256v1",
  });
  const jwk = publicKey.export({ format: "jwk" });
  const uncompressedPoint = Buffer.concat([
    Buffer.from([0x04]),
    Buffer.from(jwk.x, "base64url"),
    Buffer.from(jwk.y, "base64url"),
  ]);
  const encodedPoint = crypto.ECDH.convertKey(
    uncompressedPoint, "prime256v1", undefined, undefined, pointFormat,
  );
  const unsigned = { trace_id: "synthetic-signature-regression", events: [] };
  const signatureBytes = crypto.sign("sha256", Buffer.from(canonicalize(unsigned), "utf8"), {
    key: privateKey,
    dsaEncoding: "ieee-p1363",
  });
  const bundle = {
    ...unsigned,
    signature: {
      alg: "es256",
      canonicalization: "JCS",
      kid: "fixture-p256",
      sig: signatureBytes.toString("base64url"),
    },
  };
  const keyring = new Map([[
    "fixture-p256",
    { alg: "es256", public_key_b64url: encodedPoint.toString("base64url") },
  ]]);
  return { bundle, keyring };
}

for (const format of ["uncompressed", "compressed"]) {
  test(`ES256 verifies a valid ${format} SEC1 P-256 key from the shared keyring format`, () => {
    const { bundle, keyring } = signedFixture(format);
    assert.deepEqual(verifyTraceBundleIntegrity(bundle, keyring), []);
  });
}

test("ES256 rejects a tampered signed bundle", () => {
  const { bundle, keyring } = signedFixture();
  bundle.trace_id = "tampered";
  assert.match(verifyTraceBundleIntegrity(bundle, keyring).join(" "), /verification failed/);
});

test("ES256 fails closed for an invalid public_key_b64url point", () => {
  const { bundle, keyring } = signedFixture();
  keyring.set("fixture-p256", { alg: "es256", public_key_b64url: "AA" });
  assert.match(verifyTraceBundleIntegrity(bundle, keyring).join(" "), /not a P-256 point/);
});

test("ES256 reports an absent shared-format key field", () => {
  const { bundle, keyring } = signedFixture();
  keyring.set("fixture-p256", { alg: "es256", public_key_pem: "not-the-shared-format" });
  assert.match(verifyTraceBundleIntegrity(bundle, keyring).join(" "), /no public_key_b64url/);
});
