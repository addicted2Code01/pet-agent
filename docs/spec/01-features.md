# 1. Features

Priority key: **MVP** = needed for a first paid product. **V2** = next. **Later** = valuable, not yet.

- **★** marks a differentiator: something no competitor we found offers ([00 §0.3](00-product-offering.md#03-why-it-wins)).
- **06 #n** is the feature's rank in the [feature research](06-feature-research.md).

Every feature below is a core capability. How it's surfaced (screen, chat, voice, MCP tool, bot command) is an adapter concern; see [03-core-architecture.md](03-core-architecture.md). Setup and onboarding are in [1.12](#112-setup--onboarding); what we deliberately leave out is in [1.13](#113-deliberately-not-building); the care thread, where the owner sees and corrects the AI's answers, is in [1.14](#114-care-thread--ai-oversight).

## 1.1 Accounts, people & access

| Feature | Priority | Notes |
|---|---|---|
| Sign up, sign in, multiple accounts per user | MVP | A sitter has one login across every family they work for. |
| Account members with roles: owner, admin, family, caregiver | MVP | See [04-permissions-privacy.md](04-permissions-privacy.md). |
| Invite family and other members by QR code or link, approved by an owner | MVP | A join grant with the member's role ([08 §8.7](08-home-and-cloud.md#87-joining-by-qr)). |
| **Sitter join by QR**: a code the owner sends, shows on a screen or prints gets a sitter set up in about a minute, with no app, password or sign-up form. A second factor binds it to the right person: a code to the contact the owner entered, or the owner's approval. | MVP | Each sitter becomes a lightweight user whose access is bounded by the trip and revocable at once (Q11, revised). Cloud sitters have one login across households ([08 §8.5](08-home-and-cloud.md#85-identity-and-sign-in), [§8.7](08-home-and-cloud.md#87-joining-by-qr)). Revealing a door code needs a step-up ([04 §4.2](04-permissions-privacy.md#42-time-boxed-access)). 06 #4. |
| **Linked devices**: owners see every person's devices, and revoke one device or a whole person, effective on the next request | MVP | A device joined in one household never opens another ([08 §8.5](08-home-and-cloud.md#85-identity-and-sign-in)). |
| **Owner approval** of new devices, with match words shown on both screens | MVP | The join check for printed cards and sitters with no contact on file ([08 §8.6](08-home-and-cloud.md#86-home-sign-in-options)). |
| **Security log**: every join, approval, step-up, door-code reveal and revocation, visible to owners | MVP | Kept at least 1 year. |
| ★ **Engagements**: time-boxed care jobs granting a caregiver access to chosen pets and sites | MVP | Access opens shortly before the job starts and closes after it ends. 06 #12. |
| **Trip setup**: dates, sitter and pets in one flow, producing the sitter's join link and QR, the care plan for the stay and a readiness check | MVP | The "going away" journey ([00 §0.5](00-product-offering.md#05-core-journeys)). |
| Visit types: drop-in visits (with planned windows), overnight stays, boarding at another site | MVP | |
| **"I'm home" handback**: the owner ends the engagement; the sitter's access closes and both get the stay summary | MVP | Replaces the "text me when you're back" ritual. 06 #23. |
| Proof of care: every completed task is timestamped, with optional photo evidence | MVP | Proof without tracking anyone. 06 #17. |
| Visit check-in/out with optional geofence confirmation | V2 | Opt-in per engagement (Q12). 06 #17. |
| Hand-over notes between caregivers | V2 | |
| Professional-sitter accounts managing many client households | Later | Possibly a B2B tier; see open questions. |
| Clinic, boarding and daycare accounts sharing records with owners | Later | Cross-account sharing. |

## 1.2 Sites & places

| Feature | Priority | Notes |
|---|---|---|
| Multiple sites per account (home, vacation home, clinic, boarding, daycare, vehicle, park) | MVP | Each has an address, time zone and optional geo point. |
| Owned vs. external sites | MVP | "Happy Paws Clinic" is a site the account references but doesn't own. |
| Nested places to any depth: room → furniture → shelf → container | MVP | For example Kitchen → Pantry → Shelf 2 → Blue airtight container. The UI suggests three levels (Q5). |
| Photos and descriptions on places ("the basket by the front door") | MVP | |
| ★ Site access info (entry instructions, parking, alarm, lockbox) as secrets, with a photo of where the lockbox or keypad is | MVP | Every reveal is logged for the owner. 06 #13. |
| Portable containers (carrier, go-bag, car kit) whose contents move with them | V2 | A container place backed by an item. |
| Floor-plan or room map view | Later | |

## 1.3 Pets

| Feature | Priority | Notes |
|---|---|---|
| Pet profile: name, species, breed, sex, birth date, color/markings, microchip, photos | MVP | |
| Where the pet is now: which site, optionally which place, with history | MVP | "Sonic is at the clinic." "Biscuit is in the bathtub (storm)." |
| Favorite and usual spots | MVP | Modeled as knowledge linked to places. |
| Diet: foods, amounts, restrictions, allergies | MVP | Foods are items; amounts are in care routines. |
| Behavior and temperament notes, handling tips, triggers | MVP | Knowledge entries. |
| Vaccination certificates and vet documents on the pet profile | MVP | Boarding and daycare ask for proof. 06 #16. |
| Weight log | V2 | 06 #16. |
| Health records: conditions, structured vaccinations with due dates, vet visits | V2 | 06 #16. |
| Insurance and registration documents | Later | |

## 1.4 Items, supplies & inventory

| Feature | Priority | Notes |
|---|---|---|
| Items: toys, equipment, food, medications, cleaning supplies, documents | MVP | Categorized with a category tree. |
| Home place (where it belongs) vs. last seen (where it actually is) | MVP | "The hedgehog lives in the toy bin but was last seen under the couch." |
| ★ **Find anything**: "where is X?" across items, places, aliases and photos | MVP | Aliases matter: "ear medicine" = Methimazole. Our least-evidenced bet: validate in interviews before investing beyond MVP (06 #15). |
| Quick add by photo: snap an item, name it, pick where it lives | MVP | Fast setup. 06 #6. |
| Movement history | MVP | |
| **Supply levels** per place: plenty / low / out, with exact counts optional (count, weight, volume) | MVP | Counting is the heavy part for households. 06 #18. |
| Shopping list: marking a supply low adds it; counted supplies can use thresholds | MVP | 06 #18. |
| Record consumption (manually, or automatically from completed tasks) | V2 | Feeding uses ½ can and decrements stock. |
| Product catalog with barcode, brand and default photo | V2 | Scan to add or restock. |
| Expiry dates (food, medications) | V2 | |
| Photo recognition: "what's this / where does it go?" | Later | Vision port. |
| Reorder integrations (online stores, pharmacies) | Later | |

## 1.5 Medications (safety-critical)

| Feature | Priority | Notes |
|---|---|---|
| Structured medication orders: drug, strength, dose, route, frequency, scheduled vs. as-needed (PRN), start/end, prescriber | MVP | Plus the owner's verbatim instructions. Fractional doses (½ tablet), ml by syringe and clicks. 06 #11. |
| Safety limits: minimum interval between doses, maximum doses in a rolling window (e.g. 2 in any 24 hours), "not before" date/time | MVP | "Cerenia: not before Tue Nov 3, 08:00." |
| ★ **Can I give it now?**: a computed answer with the reason and the next allowed time | MVP | Never left to an LLM. In chat and texts it's a fixed answer line the AI can't change ([03 §3.8.4](03-core-architecture.md#384-keeping-answers-grounded)). Our lead feature. Answers "yes", "not yet", or "can't confirm" when it can't be sure the dose history or the device's clock is current, and fails closed ([07 §7.7](07-portable-core.md#77-where-answers-are-authoritative)). 06 #7. |
| A dose that already happened is always recorded; if it broke the limits, the owner and caregivers are alerted at once | MVP | Never refused, so the history stays true and later answers stay right. |
| **Medication reminders** that persist until answered, with Taken / Snooze / Skip from the notification | MVP | See 1.6. 06 #1. |
| Administration log: given, partial, refused, spat out, vomited, skipped, with dose, by whom, when | MVP | Shared with every caregiver. 06 #2. |
| **If missed / if refused** instructions per medication, shown when a dose is late or refused | MVP | E.g. "Don't double up. Call the vet if two doses are missed." 06 #8. |
| Owner alerted at once when a dose is refused, skipped, spat out or missed | MVP | 06 #8. |
| Scheduled dose changes (tapering) from dated revisions | MVP | 06 #11. |
| Medication item linkage: which bottle or pen, where it's kept, photo of the label | MVP | Label photos are sensitive (name and address). |
| Administration tips (pill pockets, mix in food) and fallbacks (gabapentin if refusing) | MVP | Knowledge linked to the order. |
| Dosage-change history with who changed it | MVP | Audit trail. |
| Refill tracking and remaining-dose estimate | V2 | 06 #18. |

## 1.6 Care routines & daily tasks

| Feature | Priority | Notes |
|---|---|---|
| Care routines: feeding, medication, walk, litter, grooming, play, cleaning, custom | MVP | |
| Calendar recurrence in the site's local time (daily 08:00 and 20:00; weekdays) | MVP | RFC 5545 RRULE. |
| Interval recurrence anchored on the last completion ("every 8 h after the last dose") | MVP | Medications need this. |
| Time windows and grace periods (due 07:00–09:00) | MVP | Drives on-time / late / missed. |
| **Reminders that persist until answered**: before the due time, then repeating until someone responds, with Taken / Snooze / Skip from the notification | MVP | Moved from V2 (Q15). 06 #1. |
| Escalation: if nobody answers, alert the owner, then a backup contact | MVP | Per routine; on by default for medications. 06 #1. |
| **Shared log**: every completion shows who did it and when, and clears everyone's reminder for it | MVP | Answers "did anyone feed the dog?" for the whole family. 06 #2. |
| Today view: done, due, overdue, upcoming, and **what's next** | MVP | A computed core query. 06 #9. |
| Complete, skip (with reason) or snooze a task; attach note or photo evidence | MVP | |
| Routines active only during an engagement or at a specific site | MVP | Different routine when boarding. |
| Visit checklist generated from the tasks due during a visit window | V2 | |

## 1.7 Knowledge, contacts & emergencies

| Feature | Priority | Notes |
|---|---|---|
| Knowledge entries on any subject (account, site, place, pet, item, medication order) | MVP | Categorized; with photos. |
| Sensitivity levels: normal, private (owner/family only), secret (encrypted, access-logged) | MVP | |
| Version history on knowledge | MVP | Who changed instructions and when. Every other record has history too (1.10). |
| What's normal for this pet: baseline quirks (hairballs, limping after naps) so a sitter can tell normal from worrying | MVP | Knowledge of kind `baseline`. 06 #5. |
| Contacts: vets, emergency vet, owner, neighbors, groomer, walker | MVP | With roles, linked pets and sites, and tap-to-call. |
| **Emergency card**: vets, emergency vet, owner contacts, critical notes, active medications and vet authorization on one screen | MVP | 06 #5. |
| **Vet treatment authorization** per engagement: whether the sitter may approve treatment, a spending limit, exclusions (e.g. euthanasia), and whether to try the owner first | MVP | Replaces the paper vet-release form. 06 #10. |
| Emergency playbooks: lost pet, vomiting, injury, toxin ingestion, fire | MVP | Structured steps plus contacts, with clear "watch and wait" vs. "call the vet now" thresholds. 06 #5. |
| Incident reports by caregivers (severity, notes, photos) that alert the owner | MVP | "Vomited twice today." 06 #14. |
| **Care sheet**: everything a sitter needs on one page, printable | MVP | Door codes are never printed. 06 #20. |

## 1.8 Activity, reporting & notifications

| Feature | Priority | Notes |
|---|---|---|
| Activity feed: tasks completed, meds given, moves, stock changes, incidents | MVP | From the event log. |
| Photo and short video updates, and visit / daily reports to the owner, pushed as they happen | MVP | Generated from events; an AI may write the prose. Video limits: Q35. 06 #3. |
| **Stay summary** at handback: what was done, on time or late, photos, incidents | MVP | 06 #23. |
| **Push notifications** for reminders, escalations, refused or missed doses, urgent incidents and photo updates; email as backup | MVP | Email-only updates get missed (06 #3). Decided (Q15). |
| Reminders for sitters without the app: SMS for medications, email or web push for the rest | MVP | SMS is metered like AI ([03 §3.10](03-core-architecture.md#310-ai-usage-metering)). |
| SMS sender numbers from a pool, one per sitter and household, so a reply from a sitter with two households reaches the right one | MVP | Ambiguous replies are never applied; "STOP" affects one sender only ([08 §8.9](08-home-and-cloud.md#89-the-owner-away-from-home)). |
| **Discreet notifications**: hide medication names on the lock screen | MVP | 06 #24. |
| Notification preferences: channels, quiet hours, discreet mode | MVP | Medication reminders can be set to override quiet hours. |
| Notifications on WhatsApp and Discord | V2 | The same channels as the care thread (1.14). Slack and Telegram later. |
| Export (PDF care sheet, CSV) | V2 | The printable care sheet is MVP (1.7). |

## 1.9 Interfaces (adapters, not core)

| Interface | Priority | Notes |
|---|---|---|
| Public API (HTTP) | MVP | Every other interface uses it, or embeds the core directly. |
| Web app: owner management + caregiver view | MVP | |
| Owner and family app with reliable push | MVP | Native shell or PWA; see Q21. |
| **Sitter web view** from a link, no install: today's checklist, can-I-give-it, where-is, emergency card | MVP | 06 #4. |
| Read-only offline copy of the care guide and emergency card on the sitter's phone; doses and task completions queue while offline | MVP | Needs a secure (HTTPS) origin. Holds no codes, tasks only 48 hours ahead, and is encrypted under a key the server leases for 24 to 48 hours. Queued entries are never lost when a trip ends ([08 §8.8](08-home-and-cloud.md#88-revocation-ending-and-late-doses)). Full offline editing V2 (Q14). 06 #19. |
| AI assistant: natural-language Q&A and actions over core queries/commands | MVP | Grounded in the household's data ("where's the leash?", "can I give it now?") plus setup help; no diagnosis. Its answers to sitters appear in the care thread, where the owner can correct them (1.14). 06 #21. |
| MCP server exposing core queries/commands as tools | V2 | Can run on the owner's own machine against the cloud API; adds no model cost. |
| Chat channels for the care thread and the assistant: WhatsApp, Discord | V2 | Two-way SMS is MVP (1.14). Slack and Telegram later. Each channel gets its own privacy review. |
| Voice (smart speaker) | Later | |

## 1.10 Platform

| Feature | Priority | Notes |
|---|---|---|
| **Notification delivery monitoring**: track every reminder from sent to answered; fall back to another channel and alert us when delivery degrades | MVP | Reliability is the product (principle 10 in the [README](README.md)). 06 #1. |
| **Record history**: every change to any record is kept with who, when, why and through which channel; any version can be restored; wrong facts are marked as errors, never erased | MVP | Edits check the version they started from, so nothing is silently overwritten ([02 §2.1](02-domain-model.md#versions--history)). |
| **Portable core**: one TypeScript build of the safety logic runs on the server, in browsers and the app shells, and later in iOS, Android and .NET native components, giving the same answers everywhere | MVP | Checked on every engine by one conformance suite ([07](07-portable-core.md)). |
| Time-zone updates shipped as signed data, without an app release | MVP | Six tzdb releases in 2026 so far; one gave five days' notice ([07 §7.5](07-portable-core.md#75-time)). |
| Audit log of sensitive reads (secrets, label photos) | MVP | |
| Data export and account deletion | MVP | Privacy law and trust. |
| Backups and point-in-time restore | MVP | |
| Per-account capability routing: which provider serves the model, vision, media and keys, by data sensitivity | MVP | Cloud providers only at first; see [03 §3.9](03-core-architecture.md#39-deployment-and-placement). |
| Edge node: run the model and vision, and keep private media and chosen secret keys, on the owner's own hardware | V2 | Dials out to the cloud; no port forwarding. |
| Engagement readiness check: warn the owner if something a sitter needs is missing or offline | MVP | Part of trip setup (1.1). Checks for home-held keys arrive with the edge node (V2). |
| **Home edition**: the core and household data on the owner's always-on Mac, Windows PC or NAS, reached through Pawsitter's relay at its own HTTPS name, or standalone (below) | V2 | The beta covers the container image and macOS; GA adds Windows and the tray app ([08](08-home-and-cloud.md)). The original prototype's local-first story. |
| Companion services for connected home installs: relay, DNS and certificates, push relay, messaging bridge, model proxy, watchdog, updates | V2 | They hold operational records such as routing data and ciphertext, not care records, except a discreet backup reminder schedule ([08 §8.14](08-home-and-cloud.md#814-what-each-companion-service-stores-and-sees)). |
| Home outage fallbacks: backup reminders from the cloud and door codes staged on the sitter's phone | V2 | A home trip isn't "ready" until each door code a sitter needs can be staged or has a stated fallback; a medication trip also needs backup reminders ([08 §8.10](08-home-and-cloud.md#810-outages-and-availability-at-home)). |
| Home backups: encrypted off-site backup of the structured data, and restore onto new hardware under the same name | V2 | Free ([08 §8.12](08-home-and-cloud.md#812-backups-keys-and-recovery-at-home)). |
| **Standalone mode** for home installs: no Pawsitter services; uses what the owner sets up, such as Tailscale or their own domain to reach the install, a Discord bot and email for notifications, and their own backup target | V2 | Decided 2026-11-07. What replaces each companion service, and what's missing: [08 §8.15](08-home-and-cloud.md#815-standalone-mode). Timing Q33, price Q34. |
| Billing and plans: Free and Plus | V2 | Proposal in [00 §0.7](00-product-offering.md#07-packaging-proposal). AI allotments ship in MVP regardless; see 1.11. |

## 1.11 AI usage & allotments

| Feature | Priority | Notes |
|---|---|---|
| Meter every hosted model call: tokens, our cost and the credits charged | MVP | One gateway in the core; see [03 §3.10](03-core-architecture.md#310-ai-usage-metering). |
| AI allotment per account per billing period, with a hard stop | MVP | Care features keep working when it runs out. |
| Onboarding credits: enough for every new account to import its care notes | MVP | A `promo` credit grant; setup should never hit a paywall. |
| SMS reminders metered on the same ledger and limits | MVP | Paid per message, like tokens. |
| Rate limits per member and per assistant turn | MVP | Stops bursts and runaway tool loops. |
| Usage meter with warnings at 80 % and 100 % | MVP | Broken down by member, purpose and model. |
| Caps per member, per engagement and per purpose | V2 | E.g. limit a sitter's AI use, or keep credits for visit reports. |
| When the allotment runs out, fall back to the owner's edge node or a cheaper model | V2 | Needs the edge node for the free fallback. |
| Paid plans and credit top-ups | V2 | Arrives with billing. |
| Reconciliation against providers' usage reports | V2 | |
| Paid overage | Later | Opt-in only; no surprise bills. |
| Bring your own provider key | Later | Recorded, not billable. Home installs get it at home GA ([08 §8.18](08-home-and-cloud.md#818-phasing)). |

## 1.12 Setup & onboarding

| Feature | Priority | Notes |
|---|---|---|
| ★ **Ready in 10 minutes**: guided setup that ends with a care guide a sitter can use | MVP | Target: median under 10 minutes ([00 §0.8](00-product-offering.md#08-mvp-scope-and-success-measures)). 06 #6. |
| Starter templates by species and situation: cat, dog, puppy, senior pet on medication | MVP | 06 #6. |
| ★ **Import an existing care note**: paste text; AI drafts routines, medications, contacts, places and notes for the owner to confirm one by one | MVP | Nothing becomes a record until a person accepts it, and medication drafts keep the source text verbatim (principle 11). Times in words ("until Tuesday morning") are worked out by the core from the note's date and shown with their weekday and date; ambiguous ones are flagged. Uses onboarding credits (1.11). 06 #6. |
| Quick add by photo for items and places | MVP | See 1.4. |
| Import from a photo of a handwritten or printed sheet | V2 | Vision port. |
| Invite family during setup, so the shared log starts on day one | MVP | The everyday habit ([00 §0.3](00-product-offering.md#03-why-it-wins)). |

## 1.13 Deliberately not building

| Not building | Instead | Why |
|---|---|---|
| General-purpose chat (group chats, media albums, calls) | The care thread (1.14) for questions, answers and corrections about care; tap-to-text for everything else | Households already text their sitters; general chat is costly to build and run (06 #22). The care thread is narrower: it exists so the owner can see and correct the AI. |
| Vet telehealth | Tap-to-call the pet's own vet and emergency vet | Funded incumbents and regulatory weight (06 #25). |
| AI diagnosis or symptom checking | Playbooks with the owner's thresholds; call the vet | False confidence is dangerous (06 #21). |
| Continuous GPS tracking of sitters | Timestamped tasks and photos; opt-in check-in in V2 | Battery drain and privacy (06 #17). |
| A marketplace for finding sitters | Bring your own sitter: friends, family or a pro | Rover and Wag own that market; we make any sitter better at the job. |
| Physical key tracking | Model a key as a tracked item if asked | A pro-sitter need (06 #26). |

## 1.14 Care thread & AI oversight

The owner sees everything the AI tells the sitter, and can correct it in the same stream, whichever channels each of them uses. Corrections fix the records, so every interface gives the corrected answer, not just the AI ([03 §3.8.2](03-core-architecture.md#382-owner-corrections), [§3.8.3](03-core-architecture.md#383-one-thread-many-channels)).

| Feature | Priority | Notes |
|---|---|---|
| ★ **Care thread** for each trip: the sitter's questions, the AI's answers, replies from the owner and family, and key events (doses logged, incidents) in one stream | MVP | In the sitter's web view, in the owner's app and on the web. |
| **Photos, videos and voice messages** in the care thread, from the app, the web or any channel; voice messages get an automatic transcript | MVP | A transcript never records anything by itself ([02 §2.11](02-domain-model.md#211-media)). Limits: Q35. |
| The owner sees every AI answer given to the sitter, live; the sitter is told the owner can see the thread | MVP | Answers can't be hidden or deleted during the trip. |
| Each AI answer shows what it was based on: the records it used and when they last changed | MVP | Makes stale data easy to spot: "Based on: Cerenia schedule, updated Oct 30". |
| ★ **Reply to correct**: the owner or family replies to an answer; it's marked "corrected" for everyone, the AI posts an updated answer, and the sitter is notified at once | MVP | Push for app users; SMS for a sitter without the app when it concerns medication. |
| **Questions for the owner**: when the records don't have the answer, the assistant says so and asks the owner; the reply goes to the sitter and can be saved to the records with one tap | MVP | The assistant never fills a gap itself ([03 §3.8](03-core-architecture.md#38-how-the-ai-assistant-plugs-in)). These always notify the owner at once. |
| **Which pet, which medication**: the core matches the names the sitter used; when they fit more than one order, the assistant asks instead of guessing, and every answer names what it checked | MVP | [03 §3.8.4](03-core-architecture.md#384-keeping-answers-grounded). |
| **Checked wording**: the AI's words beside a safety answer are checked for times, doses and yes or no; it gets one rewrite, and otherwise only the computed answer is sent | MVP | The computed answer always comes first. Pass rates are tracked as an AI quality measure. |
| The owner's correction is pinned word for word: at the top of the sitter's view, on the task it concerns, and in every AI answer about it, until it's resolved | MVP | The owner's words always outrank the AI's. |
| **Corrections update the plan**: the AI drafts the matching change (record a dose already given, revise a medication, skip a task, move an item, edit a note) and the owner applies it with one tap | MVP | The AI never changes records itself (principle 11). Once applied, the checklist, can-I-give-it and the care sheet all agree. |
| Anyone in the thread can correct the AI, including the sitter ("the leash isn't in the basket") | MVP | Applying the change follows normal permissions: a sitter can record where an item is; medication changes need the owner or family. |
| Owner notified at once of AI answers about medication, health or incidents; other answers appear in the thread and the daily report | MVP | Per trip, the owner can switch to "notify me of every answer" (Q22). |
| **One thread, every channel**: messages from the app, the website, SMS, WhatsApp, Discord and others combine into the trip's thread, each marked with where it came from | MVP | The model is channel-independent from day one. MVP channels: the app, the website (which sitters use after joining) and two-way SMS; WhatsApp and Discord in V2 (decided, Q24). |
| **Follow a trip on Discord**: the owner gets the assistant's answers, questions for them and alerts in a private channel on a server they already have, or in a direct message with the bot, and replies there to correct or answer; the sitter needn't join | V2 | Standalone installs use the owner's own bot ([08 §8.15](08-home-and-cloud.md#815-standalone-mode)); cloud and connected installs, Pawsitter's (Q24). Direct messages need the bot added to the owner's account as a user-installed app, and wait on a test ([08 §8.19](08-home-and-cloud.md#819-open-decisions-and-hypotheses)). |
| Each person chooses their channels and gets the whole thread there: a sitter on WhatsApp sees the owner's reply from Discord | MVP | One message, many deliveries; never duplicated. |
| Correct from any channel: a native reply (a WhatsApp quote, a Discord reply) targets that answer; on SMS the latest answer is assumed, or the AI asks which | MVP | |
| **Combined views**: the owner's inbox across all threads and channels, and a timeline per trip or pet merging the conversation with events | MVP | Owner and sitter each see everything they're allowed to. |
| ★ **"Why did it say that?"**: replay any AI answer with the records exactly as they were when it answered, and see what has changed since | MVP | Possible because every record keeps its history ([02 §2.1](02-domain-model.md#versions--history)). |
| How often answers get corrected, tracked as an AI quality measure | MVP | Replaying a corrected answer shows whether the records or the answer were wrong, without reading the conversation. |
| Review mode: hold the AI's medication answers until the owner approves them | V2 | For a new sitter or a risky medication (Q23). |
| A household thread for family outside trips | V2 | Members' own AI chats stay private by default ([04 §4.9](04-permissions-privacy.md#49-care-threads)). |
