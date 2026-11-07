# @pawsitter/kernel

The pure, deterministic core of Pawsitter: JSON in, JSON out, the same answer on every host. The design is in [docs/spec/07-portable-core.md](../../docs/spec/07-portable-core.md).

## What's here

- `dispatch(op, requestJson)` returns `responseJson`. Every request carries `schema_version`, and failures are stable error codes, never engine messages.
- `can_administer`: may a dose be given now? The rules are in [02 §2.8](../../docs/spec/02-domain-model.md#28-medications) and [07 §7.7](../../docs/spec/07-portable-core.md#77-where-answers-are-authoritative):
  - minimum intervals and rolling windows;
  - not-before lockouts and the order's dates;
  - dated revisions;
  - dose statuses and doses entered in error;
  - device freshness, clock checks and the skew margin.
- `self_test`: confirms strict mode is in effect in the kernel's realm.

## Build and test

```sh
npm install
npm test            # type-check, build, artifact gates, gate self-test, golden corpus on Node
npm run corpus:bun  # the golden corpus on Bun
```

The build writes two canonical artifacts to `dist/`: `kernel.js`, one strict-mode ES2017 classic script exposing `PawsitterKernel`, and `kernel.mjs`, an ES module wrapper. `manifest.json` holds their sha256 hashes.

## The rules this code follows

The kernel profile in [07 §7.4](../../docs/spec/07-portable-core.md#74-the-kernels-language-profile):
- **Host APIs:** no `Date`, `Intl`, `Math.random`, timers or other host APIs.
- **Language features:** no classes, `this`, async code, `for…in`, or functions created inside loops.
- **Numbers:** checked arithmetic on safe integers only. Instants are UTC epoch milliseconds.
- **Input:** strict validation with allowlisted keys.
- **Output:** keys in a fixed order.

`scripts/check-artifact.mjs` enforces the profile on the built script, and `test/gates-selftest.mjs` checks that those gates catch planted violations.

## The golden corpus

`corpus/<op>/*.json` holds request and response pairs, each with a description. The expected answers were computed by hand from the spec, not produced by this code. `test/run-corpus.mjs` compares responses byte for byte:
- the classic script runs in a hermetic realm, where host APIs are traps and methods newer than ES2017 are removed, with all cases in a seeded random order;
- the ES module runs the same cases in a normal realm.

Change a response in the corpus only through a reviewed change to the spec.
