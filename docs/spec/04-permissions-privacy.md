# 4. Permissions & privacy

## 4.1 Roles

| Capability | Owner | Admin | Family | Caregiver (during engagement) |
|---|:-:|:-:|:-:|:-:|
| Manage billing, delete account | ✓ | | | |
| Manage members & engagements | ✓ | ✓ | | |
| Create/edit sites, places, pets, items | ✓ | ✓ | ✓ | Items & placements only |
| Create/revise medication orders | ✓ | ✓ | ✓ | |
| Record administrations, complete tasks | ✓ | ✓ | ✓ | ✓ (engaged pets) |
| Record locations, stock changes | ✓ | ✓ | ✓ | ✓ (engaged sites) |
| Read knowledge (`normal`) | ✓ | ✓ | ✓ | ✓ (engaged subjects) |
| Read knowledge (`private`), private media | ✓ | ✓ | ✓ | |
| Reveal secrets | ✓ | ✓ | per secret | only if the engagement grants `secrets.reveal` and the secret's policy allows |
| Report incidents | ✓ | ✓ | ✓ | ✓ |
| Read activity log | ✓ | ✓ | ✓ | their own engagement's events |
| Read secret-reveal log | ✓ | ✓ | | |
| See the account's AI usage; set usage caps | ✓ | ✓ | own usage | own usage |
| Pair edge nodes; change capability routing | ✓ | | | |

Roles map to **permission sets**. Engagements and standing-caregiver memberships narrow them by **scope** (pets, sites) and **time** (engagement window). The policy check is a single core function, `authorize(caller, action, resource) → allow | deny(reason)`, used by every command and query and unit-tested as a matrix.

## 4.2 Time-boxed access

- A caregiver's access exists only within `[starts_at − access_lead, ends_at + access_lag]`.
- Outside the window, a caregiver keeps their own past events (what they did) but loses access to the household's data.
- Secrets revealed during an engagement are not cached on the caregiver's device after it ends. Clients get an expiry with every secret.
- The owner can end access early (`CancelEngagement`), which takes effect immediately.

## 4.3 Sensitivity tiers

| Tier | Examples | Handling |
|---|---|---|
| `normal` | Feeding instructions, favorite toys, place names | Visible to anyone in scope. |
| `private` | Microchip number, prescription-label photos, the owner's address, geo coordinates | Owners/family only by default; never sent to external AI adapters unless the account opts in. |
| `secret` | Door, alarm and gate codes; Wi-Fi password; lockbox code | Encrypted at rest (envelope encryption via the `Crypto` port); revealed one at a time by an explicit command; every reveal logged and visible to the owner; `assistant_access = never` by default. |

## 4.4 AI and external interfaces

- Each interface has an **egress tier**, bound to its credential ([03 §3.2](03-core-architecture.md#32-caller-context)). Integrations default to `normal`; the owner can raise one they run on their own hardware with a local model to `private`. Hosted LLMs and chat platforms (Discord, Slack) get `normal` data only, and secrets never.
- The core's own model calls are routed by sensitivity ([03 §3.9.3](03-core-architecture.md#393-routing-by-sensitivity)): `private` data only goes to providers on the owner's hardware, and a request never falls back to a provider that isn't allowed to see it.
- `Context()` builds the assistant's snapshot *after* redaction for the calling interface, so redaction can't be bypassed by asking cleverly.
- AI usage records hold token counts and costs, never prompt or reply text.
- An edge node offers only the fixed capabilities the owner turns on. Pairing it doesn't let the cloud run commands on the owner's machine.
- Writes made through AI carry `actor.integration = "assistant"` and `on_behalf_of`. Medication writes through AI require the same safety checks, and can be configured to require a tap-to-confirm in the client.

## 4.5 Media privacy

- On ingest: strip all EXIF/XMP/IPTC metadata (GPS included), re-encode, generate variants, compute a hash. Assets aren't linkable until this completes.
- Label photos (prescriptions) default to `private`.
- Signed, short-lived URLs only; no public buckets.

## 4.6 Data rights

- **Export**: all of an account's data as JSON + media, from the core's own model.
- **Deletion**: account deletion soft-deletes immediately, revokes all access, and hard-deletes after a short recovery period. Secrets and keys are destroyed first.
- **Retention**: event log and administrations kept for the account's lifetime (medical history); secret-reveal logs kept for at least 1 year.

## 4.7 Disclaimers & safety

Pawsitter is a care-coordination tool, not veterinary advice and not a medical device. `CanAdminister` enforces the *owner's own* limits; it doesn't judge whether a dose is clinically right. The UI must show the owner's verbatim instructions alongside every computed answer, and an emergency card always points to the vet and emergency vet.
