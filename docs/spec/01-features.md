# 1. Features

Priority key: **MVP** = needed for a first paid product. **V2** = next. **Later** = valuable, not yet.

Every feature below is a core capability. How it's surfaced (screen, chat, voice, MCP tool, bot command) is an adapter concern; see [03-core-architecture.md](03-core-architecture.md).

## 1.1 Accounts, people & access

| Feature | Priority | Notes |
|---|---|---|
| Sign up, sign in, multiple accounts per user | MVP | A sitter has one login across every family they work for. |
| Account members with roles: owner, admin, family, caregiver | MVP | See [04-permissions-privacy.md](04-permissions-privacy.md). |
| Invite by link or email, accept or decline | MVP | |
| **Engagements**: time-boxed care jobs granting a caregiver access to chosen pets and sites | MVP | Access opens shortly before the job starts and closes after it ends. |
| Visit types: drop-in visits (with planned windows), overnight stays, boarding at another site | MVP | |
| Visit check-in/out with optional geofence confirmation | V2 | |
| Hand-over notes between caregivers | V2 | |
| Professional-sitter accounts managing many client households | Later | Possibly a B2B tier; see open questions. |
| Clinic, boarding and daycare accounts sharing records with owners | Later | Cross-account sharing. |

## 1.2 Sites & places

| Feature | Priority | Notes |
|---|---|---|
| Multiple sites per account (home, vacation home, clinic, boarding, daycare, vehicle, park) | MVP | Each has an address, time zone and optional geo point. |
| Owned vs. external sites | MVP | "Happy Paws Clinic" is a site the account references but doesn't own. |
| Nested places to any depth: room → furniture → shelf → container | MVP | For example Kitchen → Pantry → Shelf 2 → Blue airtight container. |
| Photos and descriptions on places ("the basket by the front door") | MVP | |
| Portable containers (carrier, go-bag, car kit) whose contents move with them | V2 | A container place backed by an item. |
| Floor-plan or room map view | Later | |
| Site access info (entry instructions, parking, alarm) as secrets | MVP | |

## 1.3 Pets

| Feature | Priority | Notes |
|---|---|---|
| Pet profile: name, species, breed, sex, birth date, color/markings, microchip, photos | MVP | |
| Where the pet is now: which site, optionally which place, with history | MVP | "Sonic is at the clinic." "Biscuit is in the bathtub (storm)." |
| Favorite and usual spots | MVP | Modeled as knowledge linked to places. |
| Diet: foods, amounts, restrictions, allergies | MVP | Foods are items; amounts are in care routines. |
| Behavior and temperament notes, handling tips, triggers | MVP | Knowledge entries. |
| Weight log | V2 | |
| Health records: conditions, vaccinations, vet visits, documents | V2 | |
| Insurance and registration documents | Later | |

## 1.4 Items, supplies & inventory

| Feature | Priority | Notes |
|---|---|---|
| Items: toys, equipment, food, medications, cleaning supplies, documents | MVP | Categorized with a category tree. |
| Home place (where it belongs) vs. last seen (where it actually is) | MVP | "The hedgehog lives in the toy bin but was last seen under the couch." |
| Find anything: "where is X?" across items, places, aliases and photos | MVP | Aliases matter: "ear medicine" = Methimazole. |
| Movement history | MVP | |
| Consumable stock with units: count, weight, volume | MVP | 1 roll of poop bags; 3 cans of food. |
| Low-stock thresholds and alerts; shopping list | MVP | |
| Record consumption (manually, or automatically from completed tasks) | V2 | Feeding uses ½ can and decrements stock. |
| Product catalog with barcode, brand and default photo | V2 | Scan to add or restock. |
| Expiry dates (food, medications) | V2 | |
| Photo recognition: "what's this / where does it go?" | Later | Vision port. |
| Reorder integrations (online stores, pharmacies) | Later | |

## 1.5 Medications (safety-critical)

| Feature | Priority | Notes |
|---|---|---|
| Structured medication orders: drug, strength, dose, route, frequency, scheduled vs. as-needed (PRN), start/end, prescriber | MVP | Plus the owner's verbatim instructions. |
| Safety limits: minimum interval between doses, maximum doses per day, "not before" date/time | MVP | "Cerenia: not before Tue Nov 3, 08:00." |
| Administration log: given, partial, refused, vomited, skipped, with dose, by whom, when | MVP | |
| **Can I give it now?**: a computed answer with the reason and the next allowed time | MVP | Never left to an LLM. |
| Medication item linkage: which bottle or pen, where it's kept, photo of the label | MVP | Label photos are sensitive (name and address). |
| Administration tips (pill pockets, mix in food) and fallbacks (gabapentin if refusing) | MVP | Knowledge linked to the order. |
| Refill tracking and remaining-dose estimate | V2 | |
| Dosage-change history with who changed it | MVP | Audit trail. |

## 1.6 Care routines & daily tasks

| Feature | Priority | Notes |
|---|---|---|
| Care routines: feeding, medication, walk, litter, grooming, play, cleaning, custom | MVP | |
| Calendar recurrence in the site's local time (daily 08:00 and 20:00; weekdays) | MVP | RFC 5545 RRULE. |
| Interval recurrence anchored on the last completion ("every 8 h after the last dose") | MVP | Medications need this. |
| Time windows and grace periods (due 07:00–09:00) | MVP | Drives on-time / late / missed. |
| Today view: done, due, overdue, upcoming, and **what's next** | MVP | A computed core query. |
| Complete, skip (with reason) or snooze a task; attach note or photo evidence | MVP | |
| Routines active only during an engagement or at a specific site | MVP | Different routine when boarding. |
| Reminders before due time; escalation when overdue | V2 | Via the notification port. |
| Visit checklist generated from the tasks due during a visit window | V2 | |

## 1.7 Knowledge, contacts & emergencies

| Feature | Priority | Notes |
|---|---|---|
| Knowledge entries on any subject (account, site, place, pet, item, medication order) | MVP | Categorized; with photos. |
| Sensitivity levels: normal, private (owner/family only), secret (encrypted, access-logged) | MVP | |
| Version history on knowledge | MVP | Who changed instructions and when. |
| Contacts: vets, emergency vet, owner, neighbors, groomer, walker | MVP | With roles and linked pets/sites. |
| Emergency playbooks: lost pet, vomiting, injury, toxin ingestion, fire | MVP | Structured steps plus contacts. |
| Incident reports by caregivers (severity, notes, photos) that alert the owner | MVP | "Vomited twice today." |

## 1.8 Activity, reporting & notifications

| Feature | Priority | Notes |
|---|---|---|
| Activity feed: tasks completed, meds given, moves, stock changes, incidents | MVP | From the event log. |
| Visit / daily report to the owner, with photos | MVP | Generated from events; an AI may write the prose. |
| Notification preferences per user and channel | V2 | Push, email, SMS, chat apps: all adapters. |
| Export (PDF care sheet, CSV) | V2 | |

## 1.9 Interfaces (adapters, not core)

| Interface | Priority | Notes |
|---|---|---|
| Public API (HTTP) | MVP | Every other interface uses it, or embeds the core directly. |
| Web app: owner management + caregiver view | MVP | |
| Mobile app or PWA for caregivers, offline-capable | MVP/V2 | See open questions. |
| AI assistant: natural-language Q&A and actions over core queries/commands | MVP | Uses the assistant port; tools = core queries. |
| MCP server exposing core queries/commands as tools | V2 | Can run on the owner's own machine against the cloud API; adds no model cost. |
| Chat bots (Discord, Slack, Telegram, SMS) | Later | Each is an adapter with its own privacy review. |
| Voice (smart speaker) | Later | |

## 1.10 Platform

| Feature | Priority | Notes |
|---|---|---|
| Audit log of sensitive reads (secrets, label photos) | MVP | |
| Data export and account deletion | MVP | Privacy law and trust. |
| Backups and point-in-time restore | MVP | |
| Per-account capability routing: which provider serves the model, vision, media and keys, by data sensitivity | MVP | Cloud providers only at first; see [03 §3.9](03-core-architecture.md#39-deployment-and-placement). |
| Edge node: run the model and vision, and keep private media and chosen secret keys, on the owner's own hardware | V2 | Dials out to the cloud; no port forwarding. |
| Engagement readiness check: warn the owner if something a sitter needs (e.g. a home-held key) is offline | V2 | |
| Self-hosted edition: core and data on the owner's hardware, with a cloud relay for sitters | Later | The original prototype's local-first story. |
| Billing and plans | V2 | AI allotments ship in MVP regardless; see 1.11. |

## 1.11 AI usage & allotments

| Feature | Priority | Notes |
|---|---|---|
| Meter every hosted model call: tokens, our cost and the credits charged | MVP | One gateway in the core; see [03 §3.10](03-core-architecture.md#310-ai-usage-metering). |
| AI allotment per account per billing period, with a hard stop | MVP | Care features keep working when it runs out. |
| Rate limits per member and per assistant turn | MVP | Stops bursts and runaway tool loops. |
| Usage meter with warnings at 80 % and 100 % | MVP | Broken down by member, purpose and model. |
| Caps per member, per engagement and per purpose | V2 | E.g. limit a sitter's AI use, or keep credits for visit reports. |
| When the allotment runs out, fall back to the owner's edge node or a cheaper model | V2 | Needs the edge node for the free fallback. |
| Paid plans and credit top-ups | V2 | Arrives with billing. |
| Reconciliation against providers' usage reports | V2 | |
| Paid overage | Later | Opt-in only; no surprise bills. |
| Bring your own provider key | Later | Recorded, not billable. |
