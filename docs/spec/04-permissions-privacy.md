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
| Set vet authorization for an engagement | ✓ | ✓ | | |
| See the vet authorization | ✓ | ✓ | ✓ | ✓ (their engagement) |
| End an engagement ("I'm home") | ✓ | ✓ | ✓ | |
| Read the care thread | ✓ | ✓ | ✓ | ✓ (their engagement) |
| Correct an assistant answer | ✓ | ✓ | ✓ | ✓ |
| Apply a correction's draft | ✓ | ✓ | ✓ | only changes they could make themselves (where an item is, their tasks) |
| See the account's AI usage; set usage caps | ✓ | ✓ | own usage | own usage |
| Pair edge nodes; change capability routing | ✓ | | | |

A sitter on a guest link has the caregiver column's rights for that one engagement, limited to `normal` data (§4.2).

Roles map to **permission sets**. Engagements and standing-caregiver memberships narrow them by **scope** (pets, sites) and **time** (engagement window). The policy check is a single core function, `authorize(caller, action, resource) → allow | deny(reason)`, used by every command and query and unit-tested as a matrix.

## 4.2 Time-boxed access

- A caregiver's access exists only within `[starts_at − access_lead, ends_at + access_lag]`.
- Outside the window, a caregiver keeps their own past events (what they did) but loses access to the household's data.
- Secrets revealed during an engagement are not cached on the caregiver's device after it ends. Clients get an expiry with every secret.
- The owner can end access early with `CancelEngagement`, or by tapping "I'm home" (`EndEngagement`). Both take effect immediately.

**Sitter links** (guest access without an account, Q11):

- A link grants exactly its engagement's access: the same pets, sites, permissions and window. It holds a random token, and only the token's hash is stored.
- Revealing a secret needs a one-time code sent to the phone or email the owner entered for the sitter. Verification lasts 24 hours, and every reveal is logged against the link.
- Links never carry `private` data and can't change medication orders, routines or settings.
- The owner sees when the link was last opened and can revoke it at once. Attempts to open links are rate-limited.

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
- AI usage records hold token counts and costs, never prompt or reply text. Assistant answers to caregivers are kept only in the care thread (§4.9).
- An edge node offers only the fixed capabilities the owner turns on. Pairing it doesn't let the cloud run commands on the owner's machine.
- Writes made through AI carry `actor.integration = "assistant"` and `on_behalf_of`. Medication writes through AI require the same safety checks, and can be configured to require a tap-to-confirm in the client.

## 4.5 Media privacy

- On ingest: strip all EXIF/XMP/IPTC metadata (GPS included), re-encode, generate variants, compute a hash. Assets aren't linkable until this completes.
- Label photos (prescriptions) default to `private`.
- Signed, short-lived URLs only; no public buckets.

## 4.6 Data rights

- **Export**: all of an account's data as JSON + media, from the core's own model.
- **Deletion**: account deletion soft-deletes immediately, revokes all access, and hard-deletes after a short recovery period. Secrets and keys are destroyed first.
- **Retention**: event log and administrations kept for the account's lifetime (medical history); secret-reveal logs kept for at least 1 year. Record revisions are kept for the account's lifetime too, so any answer can be explained later; secret values are the exception and are destroyed on rotation ([02 §2.1](02-domain-model.md#versions--history)).

## 4.7 Disclaimers & safety

Pawsitter is a care-coordination tool, not veterinary advice and not a medical device. `CanAdminister` enforces the *owner's own* limits; it doesn't judge whether a dose is clinically right. The UI must show the owner's verbatim instructions alongside every computed answer, and an emergency card always points to the vet and emergency vet.

Vet authorization records the owner's instructions to their sitter. It isn't a legal consent form, and a clinic may ask for its own.

## 4.8 Printing, offline copies, notifications and import

- The printable care sheet never includes secret values; it says where to find them in the app. `private` data is printed only if the owner opts in for that print.
- The sitter's offline copy holds no secrets and expires with access: the app refuses to show it afterwards.
- Discreet mode keeps medication names and health details off lock screens and out of SMS text.
- Care-note import masks likely secrets before any hosted model sees the text, and shows the owner what will be sent ([03 §3.8.1](03-core-architecture.md#381-care-note-import)). The pasted note is deleted when the import is done unless the owner keeps it.

## 4.9 Care threads

- **Caregivers are told.** The thread shows a standing notice that the owner and family can read it, including the assistant's answers.
- **Nothing is hidden during a trip.** While the engagement is active, assistant answers can't be edited or deleted, and corrected answers stay visible, marked as corrected.
- **Thread text is stored on purpose.** It's the only place assistant text is kept; usage records still hold none (§4.4). Threads follow the activity log's retention and are included in data export. The owner can delete a thread once the engagement has ended.
- **Everything in a thread is `normal` data**, because the caregiver can read it. Hosted models may receive it under the usual egress rules, and the owner should not post private details there.
- **No secrets in threads.** The assistant never posts secret values; when asked, it points to the reveal button. If anyone types something that looks like a code or password, the app offers to save it as a secret instead and masks it before any hosted model sees it.
- **Outside engagements, a member's assistant chats are private to them.** A shared household thread is V2.
- **Channels are opt-in.** The owner chooses which channels a trip allows (app, web, SMS, WhatsApp, Discord, …), and each person links their own account on a channel with a one-time code sent through it. Messages from unlinked accounts are never accepted, and the sender learns nothing about the household.
- **Private conversations only.** A thread can be carried by a direct message or a private thread containing exactly its participants, never a group channel where others could read it.
- **Copies on other platforms.** Messages sent through SMS, WhatsApp or Discord also live on those platforms. Deleting a thread in Pawsitter can't delete those copies; the owner is told so when enabling a channel.
- **Consent.** SMS and WhatsApp need the recipient's opt-in, and replying "STOP" always works.
