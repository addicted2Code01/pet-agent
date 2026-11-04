# 7. Portable core runtime

Decided (Q13): the core is written in **TypeScript compiled to plain JavaScript**, so one build of the safety logic runs on every host: the server, the owner's own machine, browsers, app shells, and native components on iOS, Android and .NET.

Researched and verified on 2026-11-04 across five host groups: 216 fact checks (186 confirmed, 28 corrected, none refuted, 2 unverifiable), then a design pass and a red-team review. Engine facts below carry the versions they were checked against. Engines change underneath us, so the conformance suite (§7.11) re-checks them continuously.

## 7.1 Two layers

| Layer | What it is | Where it runs |
|---|---|---|
| **Kernel** | The domain logic: invariants, `can_administer`, recurrence across daylight-saving changes, what's next and overdue, authorization and redaction, version checks, metering arithmetic. Pure, synchronous and deterministic: JSON in, JSON out. `now` and new ids are passed in; it has no clock, randomness or I/O of its own. | Every supported engine, including the most limited embedded ones |
| **Core services** | The command and query handlers: load through ports, call the kernel, save, emit events. Asynchronous. | Node, Bun, Deno, browsers and WebViews; embedded engines through a host adapter (§7.9) |

The kernel is one canonical artifact per release, identified by `kernelVersion` and its sha256. A host counts as supported only after it passes the golden suite on those exact bytes.

## 7.2 What shims can and can't do

**Capabilities may be shimmed; semantics may not.** A host may supply anything that doesn't change an answer: the clock reading, randomness, timers, logging, I/O. Anything that decides a result is bundled inside the kernel or forbidden.

| Kind of gap | Remedy | Examples |
|---|---|---|
| Host capabilities | **Shim**: the host injects one `PawsitterHost` object (§7.3) | Clock, secure randomness, timers, logging, storage and other ports, digests and signatures, draining promise jobs on embedded engines |
| Anything that decides a result | **Bundle** inside the kernel | Time-zone rules from a pinned tzdb snapshot, zone-name aliases, recurrence, calendar math and ISO parsing, exact decimals, deterministic ordering, stable error codes |
| Missing syntax or packaging | **Build-time** transform | One strict-mode classic script with ES2017 syntax; the time-zone database compiled into data; an ES5 variant only if a legacy engine must be supported |
| Making hosts agree with each other | **Not feasible** | A page can't replace the browser's time-zone data; pure JS can't produce secure randomness; App Store apps get no JIT for JavaScriptCore; there is no JavaScriptCore on watchOS; ClearScript doesn't run on iOS or Android |

**Why time zones can't be shimmed:** every host's `Intl`, `Date` and `Temporal` read that host's own time-zone data, and the hosts disagree today:

| Host | Time-zone data |
|---|---|
| Node 22.23.4 / 24.22.2 / 26.13.0 | tzdb 2026e |
| Bun 1.4.4 on Linux | about 2026a |
| Chrome for Testing 153 | 2025c |
| ClearScript 7.5.1.1, Deno 2.9 | 2025b (ICU 77) |
| Firefox 159.0.1 | 2026f |
| Jint | The OS, through .NET `TimeZoneInfo` |
| Hermes on Android | The OS, through `java.util.TimeZone` |
| Apple platforms | The OS's ICU plus over-the-air time-zone updates |
| QuickJS | No `Intl` at all |

For a dose at 09:00 on 2026-11-15 in Vancouver (permanently UTC−7 since tzdb 2026b), Node shows 09:00 while Bun and Chromium show 08:00. Temporal polyfills and RRULE libraries read the host's `Intl`, so polyfilling doesn't help either. Even `Math.pow` with integer exponents returns different results across V8 versions, JavaScriptCore and Jint, so it's banned in the kernel rather than shimmed.

## 7.3 The host interface

There's one injection point, `createCore(host, kernel)`. Core services receive one frozen `PawsitterHost` object, built in JavaScript from plain wrapper functions, and never read or patch globals. The kernel receives no host object at all; it is called only through `dispatch()`.

| Member | Provides | Notes |
|---|---|---|
| `clock` | `nowMs()`: integer epoch ms | Services pass `now` to the kernel as data. When online, they also record server time for the dose audit. |
| `random` | `hex(nBytes)`: secure random bytes | Never `Math.random`. Sources: `crypto.getRandomValues`, `SecRandomCopyBytes`, `SecureRandom`, `RandomNumberGenerator`. |
| `scheduler` | `set(delayMs, fire)`, `clear(id)` | Timers for retries and timeouts only. Reminders that must fire in the background go through `notifier`. |
| `log` | `write(level, event, fieldsJson)` | Event codes and opaque ids only, through a field allowlist; no medication names or tokens. |
| `repository` | `get`, `put(key, valueJson, expectedVersion)`, `query` | Optimistic concurrency ([02 §2.1](02-domain-model.md#versions--history)). |
| `blobStore` | `put`, `get` with base64 content | Names limited to `[A-Za-z0-9._-]`, never `..`. |
| `secureStore` | Tokens and keys | Keychain, Android Keystore, DPAPI. The blob store is not a secret store. |
| `notifier` | `schedule`, `cancel`, `send`, each returning a status per reminder | `scheduled`, `inexact`, `permission_denied` or `capped`, so the app can warn (§7.9). |
| `modelGateway` | `request`, and pull-style streaming | Output is untrusted: it becomes drafts that a person confirms ([03 §3.8.1](03-core-architecture.md#381-care-note-import)). |
| `crypto` | `sha256Hex`, `hmacSha256Hex`, `verify` | Web Crypto's `subtle` is missing on insecure origins, so native or bundled implementations back it. |
| `serverTime`, `connectivity`, `lifecycle` | Trusted time and online/background signals | Used for freshness checks on dose history (§7.7). |
| `diagnostics` | Host, engine and versions | For triage only, never to choose a code path. |

Global polyfills are allowed only for third-party code outside the kernel (for example `Intl` formatting on engines without it), installed by the host adapter and listed. The kernel's tests run in a realm where every such global is absent or a trap (§7.11).

## 7.4 The kernel's language profile

**Artifact.** One strict-mode classic script: an immediately invoked function that exposes a single namespace, ES2017 syntax, no module syntax, with `'use strict'` inside the function body as well as at the top. Hosts load it unchanged: JavaScriptCore's `JSContext` has no public module API, Hermes V1 has no module loader, and the AndroidX sandbox returns only strings. An ES module wrapper is a second canonical artifact with its own hash, generated at build time.

**Boundary.** `dispatch(op, requestJson)` returns `responseJson`. Numbers that cross it are safe integers only. Ids, instants (ISO 8601 in UTC) and decimals are strings. Failures are stable error codes, never engine messages. Output keys come in a fixed order, and collections are arrays sorted by explicit keys.

**Allowed:** plain functions, plain JSON objects and arrays, `Map` and `Set`, integer arithmetic on safe integers through checked helpers, ASCII strings compared by code unit, `JSON` on plain data, ES5 regular expressions on ASCII input, and the kernel's bundled modules.

**Forbidden:**
- Host APIs: `Intl`, `Temporal`, `toLocale*`, `localeCompare`, all of `Date`, `Math.random`, timers, `fetch`, `TextEncoder`, `URL`, `structuredClone`, `console`, and any `typeof` check on a global.
- Floating-point domain math: `Math.pow` and `**`, `exp`, `log`, trigonometry, `hypot`, `cbrt`; `toFixed` or `parseFloat` on fractions. Decimals go through the decimal module.
- `async`, promises, generators, classes, `this`, `Proxy`, `eval`, `new Function`, `WeakRef`, BigInt.
- Creating any function inside a loop body. Hermes V1 shares loop bindings per function call by default, so a stored closure sees the last value. `no-loop-func` doesn't catch this, so the kernel needs a custom lint rule.
- `sort` without a total-order comparator with a unique tie-break; Unicode-version-dependent operations (`normalize`, non-ASCII case mapping, `trim` on non-ASCII text); recursion that grows with input; module-level regular expressions with the `g` or `y` flag; top-level `let`.
- `Object.assign`, `for…in` or key-by-key copies of untrusted input, which `__proto__` keys can exploit.

**Input safety.** Every request is validated against a strict schema with allowlisted keys before the kernel uses it. `__proto__`, `constructor` and `prototype` are rejected anywhere. Lookup tables keyed by input are `Map`s or null-prototype objects. Redaction projects allowed fields into fresh objects instead of deleting sensitive ones. Ill-formed UTF-16 and NUL characters are rejected. Requests are bounded: size, nesting depth, array and string lengths, decimal digits and scale, and the number of occurrences an expansion may produce.

## 7.5 Time

- **Instants are UTC epoch milliseconds.** Wall-clock time exists only through the kernel's time-zone module and a pinned snapshot.
- **The kernel is the only code that converts between instants and wall-clock time, in both directions.** Every instant it returns for display carries local fields from its snapshot (year, month, day, hour, minute, weekday, UTC offset, `snapshotId`). Apps format those fields with `Intl` set to UTC, which needs no time-zone data. User input enters as wall-clock fields plus a zone, and only the kernel converts it. Lint rules in the apps and services ban host time-zone conversion of schedule data. Without this, the Vancouver example above shows the wrong dose time on some devices even when the kernel is right.
- **Snapshots are named exactly.** `snapshotId` = tzdb version + pipeline version + sha256 (for example `2026f+p3`). Loaded snapshots are immutable and deep-frozen. Every request names the snapshot it wants, and the response echoes it. Live display uses the newest loaded snapshot; replay uses the recorded one. Each snapshot also lists, per zone, the first snapshot whose future times differ, so staleness is judged only for the zones in a request.
- **Safety rules use instants only.** Dose windows are rolling durations ("at most 2 in any 24 hours"), and `not_before` is an instant. A rule people state in calendar terms is converted to instants when it's created, with the `snapshotId` recorded. It is re-derived only through re-expansion, and caregivers are alerted if a data update moves a boundary. Sitter access windows are instants too.
- **Recurrence is stored as local wall time.** DTSTART, EXDATE, UNTIL and single-occurrence overrides are local values plus the zone, so they still match after the rules change; instants are produced only at expansion. The week starts on Monday (WKST=MO). COUNT counts occurrences before EXDATE, as RFC 5545 does, including shifted ones. EXDATE matches the wall time before any shift. Occurrences that coincide after a shift are merged and flagged. Expansions return an explicit truncation flag and continuation cursor instead of silently capping.
- **Daylight-saving gaps are a product-safety decision** (Q26). A strict RFC 5545 expander silently drops a 02:30 dose on the night clocks spring forward. Recommendation: shift it forward and flag it; in an overlap, use the first occurrence; store the policy on each schedule.
- **Zones keep the caller's original id.** It is resolved through the current snapshot's link table every time it's used; links aren't permanent (Europe/Oslo now follows Europe/Berlin). Windows zone ids are mapped with CLDR's table, `Etc/Unknown` is rejected, and `Etc/GMT±N` ids are never built from an offset, because their sign is inverted.
- **The time-zone pipeline.**
  - Data: a pinned IANA release, compiled with `zic` from the same release. Only the 64-bit TZif data is used, without leap seconds. The full RFC 9636 footer grammar is supported, results are compared with `zdump` for every zone through 2100, and invariants are checked when a snapshot loads.
  - Signing: snapshots are signed with ECDSA P-256 / SHA-256 (IEEE P1363 encoding). A signed manifest carries `snapshotId`, schema version, sha256, minimum kernel version, issue and expiry dates. Older snapshots are refused, and keys live in a KMS with rotation.
  - Release: CI prepares each snapshot, but a person approves the diff of affected zones and schedules before it's signed, and it rolls out in stages.
  - Updates ship as data without an app release. That matters: there were six tzdb releases in 2026 by October, and 2026f gave Cuba five days' notice.

## 7.6 Numbers

- Milliseconds, counts and versions are integers, through helpers that assert every result is a safe integer.
- Decimals follow one canonical grammar: optional minus sign, no leading zeros, optional fraction, no exponent, bounded digits, no negative zero. Input is validated against it before any arithmetic.
- Arithmetic uses big.js 7.0.1 in strict mode. Output always uses `toFixed(scale, roundingMode)` with each field's fixed scale, and there's one immutable constructor per rounding policy. By default big.js switches to exponential notation and shares precision settings globally, which would break canonical output.

## 7.7 Where answers are authoritative

The same kernel runs on the server and on devices, but not with the same authority.

- **The server is authoritative** for authorization, redaction, metering and the dose audit trail. It builds the caller's identity, role, access window and policy from its own records and clock, never from the request. Results computed on a device are advisory, for display and offline use, and the server re-checks them on sync.
- **Offline copies** hold only data already redacted for that sitter's access, and they expire.
- **Dose safety fails closed.**
  - Every administration is an append-only event: event id, device id, device time, server-received time, kernel sha256 and `snapshotId`. Events never go through optimistic version checks, so a dose that really happened can't be lost in a conflict.
  - `can_administer` answers `allowed`, `denied` (shown as "not yet") or `unverified`, always with reasons. It's unverified when the dose history hasn't been confirmed by the server recently enough, or a clock looks wrong; for example, a device's `now` earlier than the last recorded dose. It widens intervals by a clock-skew margin for doses recorded on other devices. An error or an unverified answer means no dose without explicit confirmation.
  - A dose that already happened is always recorded as it happened. If it broke the limits, it's flagged and the owner and caregivers are alerted at once ([02 invariant 6](02-domain-model.md#218-invariants-enforced-by-the-core)).
  - After every sync, the server looks for violations, such as two doses inside the minimum interval recorded on different devices, and alerts both caregivers.

## 7.8 Versions, replay and integrity

- **Decision records.** Every safety-relevant answer is stored with its operation, exact request bytes, kernel sha256, `snapshotId`, host and engine, and exact response bytes. Every released kernel and snapshot is kept in an immutable archive, with a replay harness pinned to a container image, so `ExplainAnswer` reproduces old answers exactly ([03 §3.4](03-core-architecture.md#34-queries-reads)).
- **Version skew.** Every request carries a schema version, and the kernel fails closed on an unknown schema version or policy field instead of ignoring it. The server enforces a minimum kernel version. A data-driven kill switch can turn off on-device computation for named kernel or engine versions, falling back to server answers.
- **Re-checking on sync.** Each client decision is replayed twice: with its recorded kernel and snapshot, to detect tampering, and with the current kernel, to flag safety discrepancies.
- **One kernel per device for what's displayed.** Widgets and watch apps render timelines that the app or server computed, written atomically into the app's shared container. They don't run their own kernel, so a widget can't disagree with its app.
- **Delivery integrity.** The kernel ships as an opaque prebuilt file that app bundlers (Vite, webpack, Metro) never transform. Web pages load it with Subresource Integrity. Native hosts check its sha256 against a signed release manifest before every load. The web app and WebView shells use a Content Security Policy without `unsafe-eval`.
- **Its own realm.** The kernel runs in a dedicated Web Worker on the web and in WebViews, a dedicated `JSVirtualMachine` on iOS, and a separate engine instance elsewhere. No UI code, library or polyfill shares its globals. A self-test runs in that realm on every web page load and on each new engine or OS version elsewhere. If it fails, safety answers become unverified and the app shows a warning.

## 7.9 Host adapters

Each embedded engine gets a native adapter that loads the kernel, owns the engine's thread and passes JSON across.

- **Never build script text from data.** Values are passed as call arguments: `JSValue.call(withArguments:)`, `callAsyncJavaScript` arguments, Jint `Invoke`, `JS_Call`, JSI calls, Javet function calls, web message ports. In the AndroidX sandbox, data goes through `provideNamedData` or a base64 literal. String concatenation into an evaluate call blocks code review. Adapters are fuzzed with quotes, backslashes, U+2028/U+2029, NUL and `</script>`.
- **Invariant locale everywhere.** Adapters format with `Locale.ROOT`, `en_US_POSIX` with a Gregorian calendar and UTC, or `CultureInfo.InvariantCulture`, and pass time as integer milliseconds. Otherwise digits, calendars and case mapping leak in from device settings (Arabic-Indic digits, Buddhist-era years, Turkish dotless i). String paths are UTF-16-safe, because Java's "modified UTF-8" and C strings break emoji in pet names. User text is normalized to NFC on the server when written.
- **Promise jobs and limits.** Each adapter drains promise jobs the way its engine needs: a loop of `JS_ExecutePendingJob` for QuickJS, `drainMicrotasks()` for Hermes, `InvokeAsync` or `ProcessTasks` for Jint, `await()` for Javet, and an explicit checkpoint after native settlements elsewhere. One owner thread per engine. Time and memory limits per engine; the instance is discarded after an interrupt, out-of-memory error or stack overflow. On the server, the kernel runs in worker threads with resource limits, so one request can't stall others.
- **A narrow surface.** Only the ports are exposed, as plain wrapper functions.
  - On iOS: a dedicated content world, with checks on the calling frame and origin.
  - On Android: web message listeners with allowed-origin rules instead of `addJavascriptInterface`.
  - QuickJS: never QuickJS's `std` or `os` modules.
  - Jint and Javet: Jint's CLR access stays off, and Javet bindings are explicit.
  - Arguments that aren't strings are rejected rather than converted.
- **Hermes flags pinned.** Block scoping, TDZ checks and the microtask queue are set identically in CI and in the app, and the self-test reports them.
- **Native notification limits.** iOS keeps only the 64 soonest pending local notifications per app. Android 12+ needs a permission for exact alarms, which Android 14 denies by default; Doze delays others; reboots clear them; Android 13+ needs notification permission. So reminders are scheduled as absolute instants, kept in a rolling window, and rescheduled on start, reboot, time or zone changes, snapshot updates and schedule edits. Server push stays the backup channel for dose reminders.

## 7.10 Supported hosts

| Tier | Host and engine (as checked) | Kernel | Services | Notes |
|---|---|---|---|---|
| MVP | Node 22 and 24 LTS (V8): cloud server and the owner's machine | Yes | Yes | Node 22 reaches end of life on 2027-04-30. An unhandled promise rejection exits the process. |
| MVP | Current Chrome, Edge, Firefox and Safari: web app and sitter link | Yes | Yes | Needs a secure context (HTTPS or localhost): on plain-HTTP LAN addresses there's no `crypto.subtle`, `randomUUID` or service worker. |
| MVP | WKWebView and Android System WebView: owner-app shell (Q21) | Yes | Yes | The bridge passes JSON strings as arguments. Current WebView builds need Android 10+. |
| V2 | JavaScriptCore `JSContext`: iOS and macOS native parts | Yes | Through an adapter | Interpreter-only in App Store iOS apps, at 1.3x to 71x slower depending on the workload (measured with JIT-less JSC in Bun); measure on devices. Microtasks drain when the outermost call returns. |
| V2 | AndroidX JavaScriptSandbox 1.1 | Yes | No | No synchronous host functions; the isolate can be terminated, so reload and retry. |
| V2 | Hermes V1 (static_h) | Yes, with pinned flags | Through JSI | Its Promise is a bundled polyfill with non-spec ordering, so services must not depend on job order. |
| V2 | Jint 4.16.4+ (.NET, pure managed) | Yes | Yes (4.5.0+ awaits correctly) | Create engines with UTC and the invariant culture. `Invoke` and `Call` don't drain jobs. |
| V2 | ClearScript 7.5 (V8) on Windows, Linux and macOS | Yes | Yes | Adapters must be fully async: blocking on a promise-backed `Task` deadlocks. No iOS or Android builds. |
| Tooling | Bun 1.4, Deno 2.9, QuickJS / quickjs-ng (incl. quickjs-emscripten) | Yes | Yes | CI engines. Bun with the JIT off approximates iOS `JSContext`; QuickJS has no `Intl` at all. |
| Not supported | watchOS (no JavaScriptCore); legacy Hermes 0.x; Jurassic, NiL.JS, YantraJS, Okojo, J2V8 | — | — | Unverified or too old. Watch apps show timelines the phone or server computed. |

The minimum OS and browser versions are still to be set (Q25).

## 7.11 Proving it: the conformance suite

- **Golden corpus.** Versioned request/response pairs for every kernel operation, compared byte for byte, each pinned to `kernelVersion`, `snapshotId` and the artifact's sha256. It changes only through a reviewed regeneration step.
- **Time-zone vectors:**
  - every 2026 release that changed future times: Moldova, Vancouver, Edmonton, Casablanca, Inuvik, Winnipeg and Havana;
  - New York's spring gap and autumn overlap;
  - half-hour and quarter-hour offsets: Lord Howe, Kathmandu;
  - aliases: Calcutta/Kolkata, Kiev/Kyiv, US/Eastern, UTC;
  - unknown ids, leap days, 2038 and 2100;
  - pairs that differ only in snapshot.
- **Domain vectors:**
  - dose windows across daylight-saving changes;
  - max-per-window edges, and `not_before` equality;
  - a `now` earlier than the last dose;
  - every-8-hours intervals across daylight-saving changes;
  - COUNT, UNTIL and EXDATE under the gap policy;
  - what's next and overdue at boundaries;
  - redaction by role, version conflicts, decimal rounding, sort ties, error codes.
- **Engine matrix in CI.** Node 22, 24 and 26; Bun with the JIT off inside an isolated `vm` context; Deno; Playwright Chromium, Firefox and WebKit; QuickJS and quickjs-ng; the Hermes V1 command-line tool with the app's flags; Jint on each target framework; ClearScript on Windows, Linux and macOS.
- **Devices.** A macOS harness for `JSContext` and WKWebView, real iOS devices at the minimum and current versions (the simulator has a JIT), and Android devices for WebView, the AndroidX sandbox and Hermes.
- **Perturbation.** The corpus is repeated under several `TZ` settings, under ar, fa, tr, th (Buddhist calendar) and ja (Japanese calendar) locales with 12- and 24-hour settings, and with older and newer host time-zone files. Host output changes; kernel output must not.
- **Hermetic realm.** A fresh realm where every global outside the allowlist is deleted, `Date`, `Intl`, `Temporal`, `Math.random`, `Math.pow`, `localeCompare`, `toLocale*`, `toFixed` and the `Function` constructor are traps, and prototype methods newer than ES2017 are removed. This catches forbidden calls reachable inside dependencies. The corpus also runs in random order inside one long-lived engine, which catches state leaking between calls.
- **Static gates.**
  - Lint and types: ESLint with the forbidden list and the function-in-loop rule; TypeScript checks only, with `isolatedModules` and `verbatimModuleSyntax` set, so esbuild compiles the same code; no `const enum` or `namespace`.
  - The artifact: parsed as an ES2017 script, with checks for `'use strict'` and that strict mode is really in effect; a scan for banned identifiers; a size budget; and its sha256 recorded in the release manifest.
- **Differential oracles at build time.** `zdump`, js-joda and moment-timezone loaded with matching data, and native Temporal on Node 26 with the same data files, compared on random instants from 1970 to 2100. Recurrence is compared with rrule-temporal and ical.js, allowing for documented policy differences.
- **Adapter contract tests.**
  - Results don't change when promise settlements are shuffled.
  - Jobs drain after every call.
  - Cancellation works and errors map to codes.
  - Unhandled rejections are reported.
  - The sandbox recovers from isolate termination.
  - Calls from the wrong thread are rejected.
- **Budgets.** p95 latency on engines without a JIT (iOS `JSContext`, Hermes, QuickJS, Jint), and a stack-depth test on a 512 KB thread.
- **Daily drill.** A job checks for a new tzdb release, regenerates the data, re-runs everything, and publishes the list of zones and schedules affected for human approval.

## 7.12 Open items

- **Decisions:** the minimum OS and browser versions (Q25), and the daylight-saving gap policy (Q26).
- **Still unverified:**
  - whether ClearScript exposes `Temporal`, and how its microtasks drain;
  - whether Jint's `Invoke` drains jobs (seen in source only);
  - `Intl` in Javet's builds without internationalization;
  - Temporal in the AndroidX sandbox on devices, and `Intl` in Hermes on iOS;
  - whether macOS JavaScriptCore follows Safari updates, and how often Apple ships time-zone updates;
  - the time-zone version in each Chrome release;
  - Deno's behavior at runtime.

  Treat these as hypotheses until the CI matrix confirms them.
- **Ownership:** the time-zone resolver, recurrence and decimal code and the data pipeline are ours to maintain. A bug there is identical on every host, so cross-engine tests can't catch it; the differential oracles and fuzzing exist for exactly that. We'll write our own time-zone resolver rather than adopt js-joda, whose classes, `Date` and `Intl` use break the kernel profile.
- **Home servers:** a sitter link served over plain HTTP from the owner's machine can't verify signatures, can't work offline, and exposes medical data to anyone on the network. Anything that shows medical data or runs the kernel needs HTTPS. How the home edition gets it is part of the home and cloud architecture.
