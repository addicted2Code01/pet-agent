# Pawsitter product spec

Status: **draft 0.7**. Decided: households first; cloud first with configurable placement; pluggable AI with metered hosted usage; an MVP feature set based on the [feature research](06-feature-research.md); owner oversight of every AI answer given to a sitter, through a care thread that combines every channel; full version history on every record; a portable TypeScript core that gives the same answers on every host ([07](07-portable-core.md)); and cloud and home editions from one codebase, with sitters set up by scanning a QR code ([08](08-home-and-cloud.md)). Open decisions are tracked in [05-open-questions.md](05-open-questions.md).

## What we're building

> **Hand off your pets' care without the worry.** Start with the [product offering](00-product-offering.md): who it's for, the hero features, how it compares, and what the MVP must prove.

A system of record for everything needed to care for pets: the places they live and visit, where every object and supply is kept, the pets themselves, their care routines and medications, and who is allowed to look after them and when.

At its heart is a **core** that knows nothing about AI, chat, MCP, Discord or any UI. Every interface (a web app, a phone app, an AI assistant, an MCP server, a chat bot) is an **adapter** that calls the same core commands and queries. Capabilities the core needs from the outside world (storage, time, files, notifications, language models, vision) are **ports**: abstract interfaces with swappable implementations.

## Documents

| # | Document | Contents |
|---|---|---|
| 0 | [Product offering](00-product-offering.md) | Who it's for, the promise, hero features, journeys, comparison, packaging, MVP measures |
| 1 | [Features](01-features.md) | Feature inventory by area, MVP vs later |
| 2 | [Domain model](02-domain-model.md) | Entities, fields, relationships, invariants |
| 3 | [Core architecture](03-core-architecture.md) | Commands, queries, events, ports and adapters |
| 4 | [Permissions & privacy](04-permissions-privacy.md) | Roles, time-boxed access, secrets, sensitive data |
| 5 | [Open questions](05-open-questions.md) | Decisions needed before building |
| 6 | [Feature research](06-feature-research.md) | What customers value in existing apps; features ranked for us |
| 7 | [Portable core runtime](07-portable-core.md) | One TypeScript kernel for every host: shims, time zones, authority, integrity, supported engines, conformance |
| 8 | [Home and cloud editions](08-home-and-cloud.md) | One codebase hosted or at home: HTTPS for home installs, QR joins, sign-in options, revocation, outages, updates, backups, companion services |

## Design principles

These come straight from lessons learned building the hackathon prototype.

1. **The core is the source of truth; interfaces are thin.** An AI answer, a bot reply and a web page about the same question must agree, because they all ask the core.
2. **Safety-critical answers are computed, never generated.** "Can Sonic have Cerenia now?", "what's overdue?" and "when was the last dose?" are answered by deterministic core queries. An AI may phrase the answer but must not do the date math or invent a dose. (The prototype's model couldn't tell which Tuesday "until Tuesday morning" meant.)
3. **Structured where it matters, free text where it doesn't.** Medications, schedules, stock and locations are structured. Personality, quirks and house rules are free-text knowledge.
4. **Time is explicit.** Instants are stored in UTC. Every site has an IANA time zone, and schedules are defined in the site's local wall time. The core takes "now" from an injected clock so everything is testable. (The prototype had a bug where the checklist reset at 8 pm because it compared UTC dates.)
5. **Privacy by default.** Access is scoped to sites and pets and limited in time. Secrets such as door codes are encrypted, revealed only to authorized people, and every reveal is logged. Location metadata (EXIF GPS) is stripped from uploaded photos. Interfaces such as AI get the minimum data needed.
6. **Everything that happens is an event.** An append-only activity log gives audit trails, visit reports, notifications, sync and analytics from one source.
7. **Offline-friendly identity.** IDs are client-generatable UUIDv7s, and records carry versions, so a sitter's phone can work offline and sync later.
8. **Placement is configuration.** Anything behind a port (the model, vision, media files, encryption keys) can run in the cloud or on the owner's own hardware, chosen per account and routed by data sensitivity. Each account's structured data has exactly one home: Pawsitter's cloud, or one home install on the owner's own computer ([08](08-home-and-cloud.md)).
9. **AI is metered and never load-bearing.** Every hosted model call goes through one gateway in the core and counts against the account's allotment. Running out pauses chat and generated prose, never care tasks or medication answers.
10. **Reliability is the product.** A reminder that doesn't fire or a log entry that disappears breaks trust faster than any missing feature; both show up in the category's worst reviews. Delivery is tracked from sent to answered, failures fall back to another channel, and drops in delivery alert us.
11. **AI drafts, people confirm.** Anything a model produces from the owner's notes enters the system as a draft. It becomes a record only when a person accepts it, and medication drafts keep the owner's exact words. Corrections work the same way: the owner's words are pinned for the sitter at once, and the matching change to the records is applied with one tap.
12. **History is never rewritten.** Every change is a new revision recording who, when, why and through which channel. Each revision records both when something was true and when the system learned it. Wrong facts are marked as errors, not erased, and edits that started from an old version are rejected instead of overwriting. So any answer can be replayed exactly as it was given.
13. **Capabilities may be shimmed; semantics may not.** The safety logic is one TypeScript kernel that runs unchanged on every host. Hosts may supply the clock, randomness, timers and storage, but never anything that decides a result: time-zone data, recurrence and decimal math ship inside the kernel, because hosts' own time-zone data disagree. The server's answers are authoritative, and answers computed on a device fail closed when they can't be sure.

## Glossary

| Term | Meaning |
|---|---|
| **Account** | A tenant: a household, a professional sitter's business, or a clinic. Owns sites, pets, items and knowledge. |
| **User** | A person who can sign in. One user can belong to many accounts, for example a sitter who works for several families. |
| **Member** | A user's membership in an account, with a role. |
| **Engagement** | A time-boxed care job: who cares for which pets at which sites, from when to when. Grants temporary access. The app calls it a **trip** when the owner is away. |
| **Sitter join** | Getting a sitter set up by scanning a QR code the owner sends, shows or prints, confirmed by a second factor. The sitter becomes a lightweight user: no app, password or sign-up form. Replaced the earlier no-account sitter link. |
| **Device** | One browser or app instance of a person. In the cloud, a **device grant** gives it access to one account, so a join in one household never opens another. |
| **Home install** | The home edition running on the owner's always-on Mac, Windows PC or NAS, holding that household's data. |
| **Home Link** | A home install's one outbound, mutually authenticated connection to Pawsitter's companion services. |
| **Relay** | Pawsitter's service that passes encrypted traffic to a home install's own HTTPS name without decrypting it, so the install works from any network without port forwarding. |
| **Companion services** | The cloud services a home install uses (relay, DNS and certificates, push relay, messaging bridge, model proxy, watchdog, updates). They hold routing data or ciphertext, not care records, except a discreet backup reminder schedule ([08 §8.10](08-home-and-cloud.md#810-outages-and-availability-at-home)). |
| **Handback** | The owner tapping "I'm home": the engagement ends, access closes, and the stay summary goes out. |
| **Site** | A real-world location with an address and time zone: a home, clinic, boarding facility, vacation home or vehicle. |
| **Place** | A spot inside a site, nested to any depth: room → furniture → shelf → container. |
| **Pet** | An animal being cared for. |
| **Item** | A physical object: a toy, equipment, food, a medication bottle, cleaning supplies. |
| **Trackable** | Anything whose location is tracked: pets and items. |
| **Home place** | Where an item belongs, its normal storage spot. |
| **Placement** | Where a trackable actually is or was last seen, with history. |
| **Stock** | How much of a consumable is at a place: a level (plenty / low / out), with an exact quantity only if the household counts it. |
| **Medication order** | A structured prescription: drug, dose, route, frequency and safety limits. |
| **Care routine** | A recurring care task definition: feeding, a medication, a walk, cleaning the litter box. |
| **Task** | One occurrence of a routine, due at a specific time, with a status. |
| **Knowledge entry** | Free-text instructions or notes attached to any subject, for example "Sonic hides under the bed when nervous". |
| **Secret** | Sensitive knowledge with stricter access: door codes, alarm codes, Wi-Fi passwords. |
| **Capability** | Something the core gets from outside through a port: a language model, vision, media storage, encryption keys. |
| **Edge node** | A small program on the owner's own machine that offers chosen capabilities to the cloud over an outbound connection. |
| **Allotment** | How much hosted AI an account may use per billing period, measured in credits, plus any extra limits. |
| **Credit** | The unit an allotment is measured in. Per-model rates decide whether credits track tokens, provider cost or a blend. |
| **Draft** | A proposed record from a template or an AI import, waiting for a person to accept, edit or reject it. |
| **Report** | An update to the owner built from events: per visit, per day, or the stay summary at handback. |
| **Care thread** | The stream for one trip where the sitter's questions, the AI's answers, the owner's replies and key events appear together. The owner sees everything in it. |
| **Correction** | A reply in the care thread saying an answer is wrong. It's pinned for the sitter until the matching change to the records is applied or dismissed. |
| **Revision** | One immutable version of a record: its values, when they took effect, when the system recorded them, who made the change and why. |
| **Channel** | A way people reach a thread: the app, the website, SMS, WhatsApp, Discord. A message is stored once and delivered on each person's channels. |
| **Channel identity** | A person's account on an outside channel (a phone number, a Discord user), verified with a one-time code before its messages are accepted. |
| **Kernel** | The pure, deterministic part of the core: one JavaScript build compiled from TypeScript, called with JSON in and JSON out, that gives the same answer on every host. |
| **Time-zone snapshot** | One pinned, signed copy of the IANA time-zone database the kernel uses, named by a `snapshotId`. Updated as data, without an app release. |
| **Decision record** | What was asked, which kernel and snapshot answered, and the exact answer, kept so any safety answer can be replayed later. |
