# Pawsitter product spec

Status: **draft 0.2**. Decided: households first, cloud first with configurable placement, pluggable AI with metered hosted usage. Open decisions are tracked in [05-open-questions.md](05-open-questions.md).

## What we're building

A system of record for everything needed to care for pets: the places they live and visit, where every object and supply is kept, the pets themselves, their care routines and medications, and who is allowed to look after them and when.

At its heart is a **core** that knows nothing about AI, chat, MCP, Discord or any UI. Every interface (a web app, a phone app, an AI assistant, an MCP server, a chat bot) is an **adapter** that calls the same core commands and queries. Capabilities the core needs from the outside world (storage, time, files, notifications, language models, vision) are **ports**: abstract interfaces with swappable implementations.

## Documents

| # | Document | Contents |
|---|---|---|
| 1 | [Features](01-features.md) | Feature inventory by area, MVP vs later |
| 2 | [Domain model](02-domain-model.md) | Entities, fields, relationships, invariants |
| 3 | [Core architecture](03-core-architecture.md) | Commands, queries, events, ports and adapters |
| 4 | [Permissions & privacy](04-permissions-privacy.md) | Roles, time-boxed access, secrets, sensitive data |
| 5 | [Open questions](05-open-questions.md) | Decisions needed before building |
| 6 | [Feature research](06-feature-research.md) | What customers value in existing apps; features ranked for us |

## Design principles

These come straight from lessons learned building the hackathon prototype.

1. **The core is the source of truth; interfaces are thin.** An AI answer, a bot reply and a web page about the same question must agree, because they all ask the core.
2. **Safety-critical answers are computed, never generated.** "Can Sonic have Cerenia now?", "what's overdue?" and "when was the last dose?" are answered by deterministic core queries. An AI may phrase the answer but must not do the date math or invent a dose. (The prototype's model couldn't tell which Tuesday "until Tuesday morning" meant.)
3. **Structured where it matters, free text where it doesn't.** Medications, schedules, stock and locations are structured. Personality, quirks and house rules are free-text knowledge.
4. **Time is explicit.** Instants are stored in UTC. Every site has an IANA time zone, and schedules are defined in the site's local wall time. The core takes "now" from an injected clock so everything is testable. (The prototype had a bug where the checklist reset at 8 pm because it compared UTC dates.)
5. **Privacy by default.** Access is scoped to sites and pets and limited in time. Secrets such as door codes are encrypted, revealed only to authorized people, and every reveal is logged. Location metadata (EXIF GPS) is stripped from uploaded photos. Interfaces such as AI get the minimum data needed.
6. **Everything that happens is an event.** An append-only activity log gives audit trails, visit reports, notifications, sync and analytics from one source.
7. **Offline-friendly identity.** IDs are client-generatable UUIDv7s, and records carry versions, so a sitter's phone can work offline and sync later.
8. **Placement is configuration.** Anything behind a port (the model, vision, media files, encryption keys) can run in the cloud or on the owner's own hardware, chosen per account and routed by data sensitivity. Each account's structured data has exactly one home.
9. **AI is metered and never load-bearing.** Every hosted model call goes through one gateway in the core and counts against the account's allotment. Running out pauses chat and generated prose, never care tasks or medication answers.

## Glossary

| Term | Meaning |
|---|---|
| **Account** | A tenant: a household, a professional sitter's business, or a clinic. Owns sites, pets, items and knowledge. |
| **User** | A person who can sign in. One user can belong to many accounts, for example a sitter who works for several families. |
| **Member** | A user's membership in an account, with a role. |
| **Engagement** | A time-boxed care job: who cares for which pets at which sites, from when to when. Grants temporary access. |
| **Site** | A real-world location with an address and time zone: a home, clinic, boarding facility, vacation home or vehicle. |
| **Place** | A spot inside a site, nested to any depth: room → furniture → shelf → container. |
| **Pet** | An animal being cared for. |
| **Item** | A physical object: a toy, equipment, food, a medication bottle, cleaning supplies. |
| **Trackable** | Anything whose location is tracked: pets and items. |
| **Home place** | Where an item belongs, its normal storage spot. |
| **Placement** | Where a trackable actually is or was last seen, with history. |
| **Stock** | The quantity of a consumable at a place, with low-stock thresholds. |
| **Medication order** | A structured prescription: drug, dose, route, frequency and safety limits. |
| **Care routine** | A recurring care task definition: feeding, a medication, a walk, cleaning the litter box. |
| **Task** | One occurrence of a routine, due at a specific time, with a status. |
| **Knowledge entry** | Free-text instructions or notes attached to any subject, for example "Sonic hides under the bed when nervous". |
| **Secret** | Sensitive knowledge with stricter access: door codes, alarm codes, Wi-Fi passwords. |
| **Capability** | Something the core gets from outside through a port: a language model, vision, media storage, encryption keys. |
| **Edge node** | A small program on the owner's own machine that offers chosen capabilities to the cloud over an outbound connection. |
| **Allotment** | How much hosted AI an account may use per billing period, measured in credits, plus any extra limits. |
| **Credit** | The unit an allotment is measured in. Per-model rates decide whether credits track tokens, provider cost or a blend. |
