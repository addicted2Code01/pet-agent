# 3. Core architecture

## 3.1 Shape: ports and adapters

```
            ┌──────────────────────── adapters (driving) ───────────────────────┐
            │  HTTP API · Web app · Mobile/PWA · CLI · AI assistant · MCP · bots │
            └───────────────────────────────┬───────────────────────────────────┘
                                            │ commands / queries (+ caller context)
                ┌───────────────────────────▼───────────────────────────┐
                │                         CORE                          │
                │  Core services: command & query handlers (async)      │
                │  Kernel: entities, invariants, recurrence, safety     │
                │  rules (can_administer, whats_next), policy           │
                │  (authorization, sensitivity, redaction), metering,   │
                │  event creation                                       │
                └───────────────────────────┬───────────────────────────┘
                                            │ ports (interfaces the core owns)
            ┌───────────────────────────────▼───────────────────────────────────┐
            │ Repository · UnitOfWork · Clock · IdGenerator · BlobStore ·        │
            │ Crypto · Identity · Notifier · EventPublisher · JobScheduler ·     │
            │ SearchIndex · Geo · LanguageModel · Vision · BarcodeLookup         │
            └──────────────────────── adapters (driven) ─────────────────────────┘
               Postgres/SQLite · S3/local disk · KMS · OIDC · APNs/FCM/email/SMS …
```

Rules:
- The core depends only on its own ports. No HTTP, SQL, LLM SDK or chat library is imported inside the core.
- **Driving adapters never touch storage.** The web app, MCP server and AI assistant all go through the same command/query API, with the same authorization.
- **The domain layer is the kernel**: pure, synchronous and deterministic, one JavaScript build, compiled from TypeScript, that runs unchanged on every host ([07](07-portable-core.md)). The server's answers are authoritative; answers computed on devices are advisory and re-checked on sync.
- **AI is an adapter on both sides.** As a *driving* adapter, the assistant turns natural language into core queries and commands. As a *driven* port (`LanguageModel`), the core may ask for prose (a visit-report summary) or for drafts that a person must confirm (care-note import, §3.8.1), but never for a fact or a decision.

## 3.2 Caller context

Every command and query carries a `CallerContext`:

```
CallerContext {
  account_id
  actor: Actor            # user / system / integration, + device and on_behalf_of
  interface: "web" | "mobile" | "api" | "assistant" | "mcp" | "sms" | "whatsapp" | "discord" | ...
  egress_tier: "normal" | "private"   # the most sensitive data this interface may receive
  transport: "loopback" | "lan" | "relay" | "tunnel" | "cloud"   # how the request arrived; recorded, never raises trust
  device_id, auth_strength   # the device grant and how it was established (passkey, code, approval, PIN)
  now: Instant            # from the Clock port at the edge, so a request is evaluated at one instant
  locale, request_id
}
```

`interface` and `egress_tier` come from the authenticated credential, never from the request. First-party apps get `private` (what a user may see is still decided by their role). A sitter is a lightweight user on the web app: their device grant limits them to their engagement's scope and the `normal` tier. `transport`, `device_id` and `auth_strength` also come from the connection and the credential; relayed traffic is never treated as local ([08 §8.5](08-home-and-cloud.md#85-identity-and-sign-in)). The owner registers each other integration, for example an MCP server on their laptop with a local model, and sets its tier; the default is `normal`.

The kernel's policy rules use `actor`, `interface` and `egress_tier` to decide access and redaction. For example, the `assistant` interface never receives secret plaintext unless the secret allows it, and private photos are replaced by placeholders for interfaces with a `normal` tier.

## 3.3 Commands (writes)

Each command validates input, checks policy, enforces invariants, writes through the `UnitOfWork`, and emits events, all atomically. Commands are idempotent when given a client `command_id` (safe retries and offline sync). A command that changes an existing record carries the `expected_version` it started from; a mismatch is a conflict, never a silent overwrite. Every write stores a revision ([02 §2.1](02-domain-model.md#versions--history)).

| Area | Commands |
|---|---|
| Accounts & access | `CreateAccount`, `ChangeMemberRole`, `RemoveMember`, `CreateEngagement`, `ConfirmEngagement`, `CancelEngagement`, `EndEngagement` ("I'm home"), `SetVetAuthorization`, `PlanVisits`, `CheckIn`, `CheckOut` |
| Joins ([08 §8.7](08-home-and-cloud.md#87-joining-by-qr)) | `CreateJoinGrant` (any role), `ClaimJoinGrant` (POST on Continue; spends the secret only when the second factor passes), `OpenJoinWindow`, `CloseJoinWindow`, `RequestToJoin`, `ApproveJoin`, `DenyJoin`, `RotatePrintedLocator`, `RevokeJoinGrant` |
| Devices and sign-in | `RevokeDevice`, `SignOutEverywhere`, `SuspendMember`, `RegisterPasskey`, `RevokePasskey`, `StepUp`, `SetPersonPin`, `LinkPawsitterAccount`, `SetHomeAuthPolicy` |
| Home installs | `PairInstallation`, `UnpairInstallation` (a soft disable for 7 days), `LockRemoteAccess`, `SetLanAccess`, `RestoreInstallation` (same install id and name) |
| Sites & places | `CreateSite`, `UpdateSite`, `CreatePlace`, `MovePlace` (re-parent), `RenamePlace`, `ArchivePlace` |
| Pets | `CreatePet`, `UpdatePet`, `RecordPetLocation`, `RecordWeight` |
| Items | `CreateItem`, `UpdateItem`, `SetHomePlace`, `MoveItem`, `RecordSighting`, `ReturnItemHome`, `ArchiveItem` |
| Inventory | `SetSupplyLevel` (plenty / low / out), `Restock`, `RecordConsumption`, `CountStock`, `TransferStock`, `SetStockThresholds`, `AddToShoppingList`, `MarkBought` |
| Medications | `CreateMedicationOrder`, `ReviseMedicationOrder`, `SetNotBefore`, `PauseOrder`, `DiscontinueOrder`, `RecordAdministration` (with the `can_administer` answer when the dose was started from the app, and the caregiver's confirmation if it was `unverified` or an error), `OverrideAndRecordAdministration` |
| Care | `CreateRoutine`, `UpdateRoutine`, `PauseRoutine`, `CompleteTask`, `SkipTask`, `SnoozeTask`, `UndoTaskCompletion` (time-limited), `AnswerReminder` (Taken / Snooze / Skip from a notification; becomes `RecordAdministration`, `CompleteTask`, `SnoozeTask` or `SkipTask`) |
| Setup | `ApplyTemplate`, `ImportCareNote`, `AcceptDraft`, `EditDraft`, `RejectDraft` |
| Notifications | `SetNotificationPreferences` |
| Care threads | `PostMessage` (from any channel), `EditMessage` (people's messages only; a new revision), `CorrectAnswer` (a reply that flags an answer as wrong), `AskOwner` (the assistant passes on a question the records don't answer), `ResolveCorrection` (applied or dismissed), `SetThreadNotifications` |
| Channels | `SetTripChannels` (which channels a trip allows), `LinkChannelIdentity` (verify with a one-time code), `RevokeChannelIdentity`, `BindThreadChannel`, `UnbindThreadChannel` |
| History | `RestoreRevision` (writes a new revision with old values), `MarkEnteredInError` (a dose, sighting, completion or stock transaction, with a reason) |
| Knowledge | `CreateKnowledgeEntry`, `ReviseKnowledgeEntry`, `ArchiveKnowledgeEntry`, `CreateSecret`, `RotateSecret`, `RevealSecret` (a command, because it's logged) |
| Contacts | `CreateContact`, `UpdateContact`, `LinkContact`, `UnlinkContact` |
| Media | `BeginUpload` → `CompleteUpload` (strips metadata, makes variants), `LinkMedia`, `UnlinkMedia`, `SetAltText`, `DeleteMedia` (removes the files; the record stays) |
| Incidents | `ReportIncident`, `AcknowledgeIncident`, `ResolveIncident` |
| AI usage | `SetUsageLimit`, `RemoveUsageLimit`, `GrantCredits` (admin), `PurchaseCredits` (V2) |
| Placement | `PairEdgeNode`, `UnpairEdgeNode`, `SetCapabilityRoutes`, `MoveSecretKey` (all V2) |

## 3.4 Queries (reads)

Queries return structured, typed results, ready for any adapter to render. The safety-relevant ones are deterministic and explain themselves. Every instant returned for display comes with local wall-clock fields computed by the kernel in the site's zone, and also in the viewer's `time_zone` when it differs ([02 §2.4](02-domain-model.md#24-identity-tenancy--access)); clients format those fields, never the instant ([07 §7.5](07-portable-core.md#75-time)).

| Query | Returns |
|---|---|
| `WhatsNext(scope = site / pet / engagement)` | Overdue tasks first, then the next due task, each with routine, pet, window and instructions. |
| `Today(scope)` | All of today's tasks (in the site's local day) with status. |
| `CanAdminister(order_id)` | `{decision, reasons, next_allowed_at, last_given_at, doses_in_window, history_confirmed_at, snapshot_id, instructions_verbatim}`. `decision` is `allowed` (shown as "yes"), `denied` ("not yet") or `unverified` ("can't confirm"), which fails closed ([02 §2.8](02-domain-model.md#28-medications)). |
| `MedicationSummary(pet_id)` | Active orders with last dose, next due and remaining stock. |
| `WhereIs(query)` | Ranked matches across pets, items, places and aliases: current placement, home place, path ("Home › Kitchen › Pantry › Shelf 2"), last seen time, photos. |
| `WhatsIn(place_id, recursive)` | Items, stock and pets at a place or subtree. |
| `PlaceTree(site_id)` | The nested place hierarchy. |
| `LowStock(scope)`, `ShoppingList()` | |
| `KnowledgeFor(subject_id, include_related)` | Entries (critical first), playbooks, linked contacts. |
| `EmergencyCard(pet_id / site_id)` | Vets, emergency vet, owner contacts, critical notes, active medications, and the vet authorization for the current engagement. Fits on one screen. |
| `CareSheet(scope, format)` | Everything a sitter needs for a pet or an engagement, as structured data or a print layout. Never includes secret values; `private` data only if the owner opts in for that print. |
| `OfflineBundle(engagement_id)` | A read-only snapshot for the sitter's device, expiring with access: the care sheet, the emergency card and tasks for the next 48 hours. For each engaged pet's medications it adds the order revisions in force over those 48 hours, every administration their limits look back over (at least the last one), `history_confirmed_at` and the time-zone snapshot, so can-I-give-it works offline, counting doses queued on the device, and answers "can't confirm" once the history is too old. No secret values ([04 §4.8](04-permissions-privacy.md#48-printing-offline-copies-notifications-and-import)); in the home edition, door codes are staged separately after a step-up ([08 §8.10](08-home-and-cloud.md#810-outages-and-availability-at-home)). |
| `Activity(scope, range)`, `Report(report_id)` | Events grouped for display; visit, daily and stay reports. |
| `Drafts(import_job_id / template_id)` | Pending drafts with their source excerpts, for the owner to accept, edit or reject. |
| `Search(text, filters)` | Full-text across names, aliases and knowledge, via the `SearchIndex` port. |
| `ResolveLocalTime(fields, reference, zone)` | The local date and time that a time given in words refers to (a weekday, a part of the day, a clock time, "tomorrow"), counted from a reference date, with every candidate when more than one fits (§3.8.4). |
| `AiUsage(scope, period)` | Used and remaining for the credit balance and each limit; breakdown by member, purpose and model; reset time; projected run-out date. |
| `Readiness(engagement_id)` | Whether the trip is ready: the sitter's device has joined; emergency vet and vet authorization set; every medication has "if missed" instructions; no supply marked out; no device that gets the trip's reminders reports a status other than `scheduled` ([07 §7.3](07-portable-core.md#73-the-host-interface)); and (V2) every capability the engagement depends on is reachable (§3.9.4). For a home install it also checks ([08 §8.10](08-home-and-cloud.md#810-outages-and-availability-at-home)):<br>- reachability and uptime;<br>- a certificate valid for more than 14 days;<br>- sleep and power settings;<br>- backup age;<br>- the newest time-zone snapshot;<br>- backup reminders on for medication trips;<br>- every door code needed outside covered by a stated fallback, or able to be staged (the sitter's device has joined and may reveal it) and staged once access opens. |
| `LinkedDevices(scope)`, `PendingJoins()`, `SecurityLog(range)` | Each person's devices and grants; joins waiting for approval; the security log of joins, approvals, step-ups, reveals and revocations. |
| `InstallationHealth()` (home) | Heartbeats and uptime, certificate and backup state, versions, the time-zone snapshot, and the Home Link's status. |
| `Context(scope, budget)` | **A compact, permission-filtered snapshot for assistant adapters**: open owner corrections word for word, first; then the current time in the site's zone, pets, today's tasks with status, active medications with `CanAdminister` results, relevant knowledge, and the recent care thread from every channel. This is the generalized "send everything in the prompt" from the prototype. |
| `Thread(thread_id, since?)` | The care thread merged across channels: messages with their sources, statuses and channel, open corrections pinned first. |
| `Inbox(viewer)` | Every thread the viewer may see (each trip's, the household's, their own direct chat), across all channels, with unread counts and open corrections. The owner's view of everything. |
| `Timeline(scope = trip / pet, viewer)` | One stream merging messages from every channel with events (doses, tasks, incidents, moves), each tagged with where it came from, filtered by what the viewer may see. |
| `OpenCorrections(scope)` | Corrections not yet applied or dismissed, with their drafts. |
| `History(subject_id)` | Every revision of a record: what changed, who changed it, when, why, through which channel, and what prompted it (a draft, a correction, an import). |
| `ExplainAnswer(message_id)` | Replays an assistant answer as of its `as_of`, with the kernel build and time-zone snapshot it recorded: the records exactly as they were, the computed results it quoted, and what has changed since. It can also re-run the answer on today's records with the same kernel and snapshot. |

## 3.5 Events

Every command emits one or more events (`2.12 Event`), stored in the same transaction (transactional outbox) and then published through `EventPublisher`. Consumers are adapters or core jobs:
- the **notifier** (task reminders, overdue escalation, refused or missed doses, low stock, urgent incidents, engagement starting)
- **report** assembly (visit, daily and stay reports)
- the **care thread** (doses, incidents and task changes appear inline, next to the conversation)
- the **search index** updater
- **sync** to offline clients
- analytics, webhooks and integrations (later)

## 3.6 Background jobs (`JobScheduler` port)

| Job | Purpose |
|---|---|
| `MaterializeTasks` | Keep calendar tasks generated N days ahead; regenerate when routines change or their instants move (a new time-zone snapshot, a site's new zone, or a pet moving to another zone), and alert caregivers when a dose time moves. |
| `ReminderDispatcher` | Send reminders by each routine's `reminder_policy`; repeat until answered; escalate to the owner, then a backup contact; withdraw a reminder on every device the moment anyone completes the task. |
| `DeliveryMonitor` | Track delivery receipts per channel; fall back to the recipient's next channel when one fails; alert us when delivery rates drop. Reliability is the product (README principle 10). |
| `TaskStatusSweeper` | Mark tasks `missed` and raise missed-dose alerts to the owner. Reads are correct without it. |
| `EngagementLifecycle` | Send the owner the readiness check a day before a trip; open/close caregiver access at window edges and at "I'm home"; activate engagement-only routines; end caregiver device grants, leaving them limited for 7 days to late uploads and reads of the sitter's own events and the stay summary ([08 §8.8](08-home-and-cloud.md#88-revocation-ending-and-late-doses)). |
| `SessionSweeper`, `JoinWindowRotator`, `PushSubscriptionSweeper` | Expire sessions and grants; rotate the nonce of open join windows every 30 seconds; delete push subscriptions the push service reports gone. |
| `ReminderCatchUp` (home) | On every start, wake or Home Link reconnect, apply the replies queued at the bridge, then take back reminders still open: fire those the bridge never sent, marked late, and continue the rest ([08 §8.10](08-home-and-cloud.md#810-outages-and-availability-at-home)). |
| `CertificateRenewal`, `LinkHeartbeat`, `Backup`, `UpdateCheck` (home) | Renew the install's certificate through ACME Renewal Information and at startup; keep the Home Link alive and report heartbeats (standalone: to the owner's monitor); take snapshots daily and before migrations, and the encrypted off-site backup; apply signed code and data updates ([08 §8.4](08-home-and-cloud.md#84-https-for-home-installs), [§8.11](08-home-and-cloud.md#811-updates-and-data-at-home), [§8.12](08-home-and-cloud.md#812-backups-keys-and-recovery-at-home)). |
| `ReportBuilder` | Assemble visit, daily and stay reports from events, and push them to the owner. |
| `ImportDrafting` | Turn a pasted care note into drafts (§3.8.1). |
| `LowStockCheck` | Raise `stock.low` and fill the shopping list. |
| `MediaPipeline` | Strip metadata, re-encode, make variants and video posters, compute hashes, and request transcripts of voice messages. A media worker does this in the cloud; at home, the home machine does. |
| `Retention` | Hard-delete soft-deleted data past retention; purge secrets of closed engagements from caches. |
| `PeriodRollover` | Start each billing period: issue the plan's credit grant and expire the previous one. |
| `ReservationSweeper` | Release usage reservations whose calls never settled (crashed workers). |
| `UsageReconciliation` | Compare the usage ledger with providers' usage reports daily; flag drift. |
| `CapabilityHealth` | Check edge nodes and providers, and add capability checks to engagement readiness (V2). |

## 3.7 Ports

| Port | Responsibility | Example adapters |
|---|---|---|
| `Repository<T>` / `UnitOfWork` | Load/save aggregates; transactions; tenant scoping built in | Postgres (cloud), SQLite (home installs, tests) |
| `Clock` | `now()` | System clock; fixed clock in tests |
| `IdGenerator` | UUIDv7 | |
| `BlobStore` | Put/get/delete media; signed URLs | S3-compatible, local disk |
| `Crypto` | Envelope encryption for secrets; key rotation | Cloud KMS, local keyfile |
| `Identity` | Passkeys, device sessions and per-account grants, one-time codes, joins and approvals, step-up; OIDC | Pawsitter ID in the cloud; the home core itself at home ([08 §8.5](08-home-and-cloud.md#85-identity-and-sign-in)) |
| `Notifier` | Deliver a message on a channel and report delivery receipts and the channel's message id | Push (APNs/FCM), web push, email, SMS, WhatsApp, Discord, Slack |
| `EventPublisher` | Publish committed events | In-process bus, queue, webhooks |
| `JobScheduler` | Run recurring and one-off jobs | Cron in-process, queue workers |
| `SearchIndex` | Full-text + fuzzy name/alias search | SQLite FTS5, Postgres full-text, Meilisearch |
| `Geo` | Geocode addresses; geofence checks | Mapping provider, none |
| `LanguageModel` | Generate prose from structured input (reports, summaries) | Local llama.cpp, Claude API, none |
| `Vision` | Describe or identify a photo ("which item is this?") | Local VLM, hosted model, none |
| `SpeechToText` | Transcribe voice messages and the speech in videos | Local model, hosted provider, none |
| `BarcodeLookup` | Barcode → product details | Product databases, none |

Every port has a **null implementation**, so the core runs fully without AI, search engines, maps or notifications. Features degrade gracefully instead of failing. On every host, these ports and the runtime members in [07 §7.3](07-portable-core.md#73-the-host-interface) (randomness, timers, logging, secure storage, digests, server time, connectivity, lifecycle and diagnostics) come in one host object. The exception is `IdGenerator`: core services build UUIDv7 ids from the host's clock and randomness.

Any port except `Repository`/`UnitOfWork` can also be served by a `RemoteCapability` adapter that forwards calls to the owner's edge node (§3.9.2). `LanguageModel` and `Vision` are only ever called through the `ModelGateway`, which routes and meters them (§3.10).

## 3.8 How the AI assistant plugs in

The assistant is a driving adapter with this loop:

1. Build a prompt from `Context(scope, budget)`: compact, current, permission-filtered.
2. Expose core **queries and commands as tools** (`whats_next`, `can_administer`, `where_is`, `complete_task`, `record_administration`, `report_incident`…), each a thin wrapper running with the user's `CallerContext` (`interface = "assistant"`, `on_behalf_of = user`). Safety tools take the pet and medication as the person said them, and the core works out which order is meant (§3.8.4).
3. The model chooses tools and phrases results. **Facts come only from tool results**: times, doses and yes-or-no answers reach people only in an answer line that code renders from the result, and the model's own words are checked (§3.8.4). When the records don't answer a question, the assistant says so and passes it to the owner (`AskOwner`) instead of guessing. The owner's reply goes back to the sitter, and the assistant drafts it as a record that the owner saves with one tap (principle 11).
4. Writes requested through the assistant ("I gave him his pill") go through the same commands, so they're validated, safety-checked and logged as *assistant on behalf of Jane*. One that records or changes a dose, a medication or a schedule waits until the person the assistant acts for confirms it ([04 §4.4](04-permissions-privacy.md#44-ai-and-external-interfaces)).
5. The assistant's own model calls go through the `ModelGateway` (§3.10), so they're routed by sensitivity and metered against the account's allotment.
6. During an engagement, every answer is posted to the care thread with its `sources` (the records and versions it used), so the owner sees it live and can correct it (§3.8.2).

An assistant the owner runs on their own hardware with a local model is just another interface with its own credential: it calls the public API like any other client, and the gateway and metering don't apply.

In MVP the assistant is scoped to grounded answers about the household ("where's the leash?", "can I give it now?", "what's next?") and to setup help. It doesn't diagnose or give medical advice; for health questions it shows the relevant playbook and the vet's number ([01 §1.13](01-features.md#113-deliberately-not-building)).

### 3.8.1 Care-note import

The other model use in MVP turns the note an owner already leaves for sitters into structured drafts:

1. **Mask.** A deterministic detector in the core finds likely secrets (door and alarm codes, passwords) and replaces them with placeholders before any hosted model sees the text. The owner is shown what will be sent.
2. **Draft.** The masked text goes through the `ModelGateway` (§3.10) with purpose `care_note_import`. The model returns proposed routines, medication orders, contacts, places and notes, each with the sentences it came from. Times given in words come back as the words and the fields the model read, never as dates (§3.8.4).
3. **Validate.** Each proposal is checked against its target's schema. Anything invalid stays a draft with the problem marked.
4. **Confirm.** The owner accepts, edits or rejects each `Draft`. Nothing becomes a record without a person accepting it (principle 11). Times given in words are resolved by the kernel against the day the note was written, which the owner confirms, and shown with their weekday and date; an ambiguous one has to be picked before its draft can be accepted. An accepted medication draft keeps its source sentences as `instructions_verbatim`, and masked secrets come back as secret drafts filled in locally from the original text.

New accounts get onboarding credits for this ([00 §0.7](00-product-offering.md#07-packaging-proposal)), so setup never hits a paywall. Owners with an edge node can route import to their local model, which may see the unmasked text.

### 3.8.2 Owner corrections

The assistant has no memory of its own. What it "knows" is the household's records, read fresh through `Context()` and the query tools on every turn. So a correction has to change the records, and once it does, every interface gives the corrected answer: the assistant, the sitter's checklist, `CanAdminister` and the care sheet. Teaching only the chat would leave the checklist still saying "give it".

**Example.** The sitter asks "What do I do next?" and the assistant answers "Give Sonic his Cerenia". The owner replies in the thread: "No, I gave it at 7 before I left."

1. **Flag.** The reply is posted as a `correction` of that answer (`CorrectAnswer`). The answer is marked *corrected* for everyone, and the sitter is notified at once: push in the app, or SMS for a sitter without the app when it concerns medication.
2. **Pin.** Until the correction is resolved, the owner's words are pinned at the top of the sitter's view, on the task they concern, and first in every assistant context for that scope (invariant 19). The assistant must show them with any computed answer they concern, and never contradict them.
3. **Re-answer.** The assistant posts an updated answer that quotes the owner: "Jane says she gave Cerenia at 7:00. Don't give it now."
4. **Draft the fix.** The assistant proposes the matching change as a `Draft` linked to the correction: here, `record` an administration of Cerenia at 07:00 by Jane. Other corrections become other drafts: revise a medication order, skip a task, move an item, revise a knowledge entry.
5. **Apply.** The owner applies it with one tap. It runs through the normal command (`RecordAdministration`, `ReviseMedicationOrder`, …) with the owner's permissions, every safety check, and the draft's `base_version` as `expected_version`. The new revision records the correction as its cause. `CanAdminister` now says "not until 07:00 tomorrow", the correction is resolved, and the pin comes down.

Rules:
- **The assistant never applies a correction itself.** It only drafts; a person allowed to make the change applies it (principle 11). An unapplied correction stays pinned, so the owner's words keep governing the sitter's view even if nobody taps Apply.
- **Even cautious corrections are drafts.** "Don't give it" never becomes an automatic hold: if the assistant misread "give it with food" as "don't give it", a hold could block a dose that matters. The owner's words are pinned instead.
- **Anyone in the thread can correct the assistant**, including the sitter ("The leash isn't in the basket"). Who can apply the resulting draft follows normal permissions: a sitter can record where an item is, but medication changes need the owner or family.
- **If the sitter already acted** on the answer, the logged dose appears in the thread next to the correction, so the owner sees it at once and can follow the medication's instructions or call the vet.
- **Corrections respect versions.** A draft is made against the record's current version. If the record changes before the owner applies it (an edit on the website, say), the draft goes stale and the assistant re-drafts against the new version. If a later edit already covers the correction, the owner is asked whether to resolve it.
- **Wrong facts are marked, not erased.** If the correction is that something recorded never happened ("he didn't get his 8:00 dose; I logged it by mistake"), the draft marks that record `entered_in_error`. The history keeps both what was believed and what was true.
- **Corrections are measured, and classified without reading the conversation.** How often answers get corrected is an AI quality measure ([00 §0.8](00-product-offering.md#08-mvp-scope-and-success-measures)). Replaying the corrected answer on the records as they are now, with the kernel build and time-zone snapshot it recorded (`ExplainAnswer`), separates the causes: if the replayed answer changes, the records were missing or wrong; if it doesn't, the answer itself was wrong. A difference that appears only with the current kernel or snapshot is a code or data change, not a record error. Reading the conversation still needs the owner's permission.

### 3.8.3 One thread, many channels

A trip has one care thread, but people reach it in different ways: the owner in the app or on Discord, the sitter in the web app, by text or on WhatsApp. Channel adapters are both driving (inbound messages become `PostMessage` commands) and driven (outbound copies go through the `Notifier` port). Which channels a trip allows is the owner's choice (`SetTripChannels`).

**Inbound.**
1. The adapter receives a message (a WhatsApp webhook, a Discord event, an incoming SMS) and looks up the sender's `ChannelIdentity`. An unknown or unverified sender gets a link to verify, and learns nothing about the household.
2. It finds the thread through the `ChannelBinding` and posts the message with its `channel`, `external_message_id` and the channel's timestamp. A repeated delivery with the same external id is dropped (invariant 23). Attachments are downloaded at once, because channel links expire, and appear once the media pipeline has processed them.
3. If the channel has native replies (a WhatsApp quote, a Discord reply), `reply_to_id` comes from the channel's message id through the delivery records. Otherwise the message is matched to the latest assistant answer sent to that person; if that's ambiguous, the assistant asks which answer is meant.
4. The message acts with the person's permissions and the channel's egress tier. Outside platforms are `normal` and never receive secrets.

**Outbound.**
- Each message is stored once and delivered to each participant on their chosen channels, as one `NotificationDelivery` per copy carrying the channel's message id.
- The assistant answers on the channel where it was asked. Other participants get the answer according to the thread's notification policy (Q22).
- Each channel renders the same message its own way. Discord and WhatsApp show an "Apply" button on a draft; SMS gets plain text with a short link that opens the draft in the app after sign-in. Photos and videos go as attachments where the channel shows them, and as a link by text; `private` media only ever go as a link.
- Channel rules belong in the adapter: WhatsApp's 24-hour reply window and approved message templates, SMS opt-out ("STOP"), Discord rate limits. Paid channels (SMS, WhatsApp) are metered like AI usage (§3.10).
- A person can follow a trip entirely in their own chat with a bot, such as an owner's private Discord channel or direct message. Their side of the thread arrives there under the notification policy, and their replies come back as messages, corrections or answers ([08 §8.15](08-home-and-cloud.md#815-standalone-mode)).

**The combined view.** `Thread`, `Timeline` and `Inbox` merge every channel into one stream, ordered by when the core received each message, with a badge showing where each came from. Both sides see the same conversation: the owner sees everything, and the sitter sees the whole trip thread, including what the owner sent from Discord, on whichever channel they use. Because `Context()` includes the merged thread, the assistant answering on WhatsApp knows what the owner said on Discord.

The **MCP server** is the same tool set exposed over MCP, so any MCP-capable client gets exactly the same safe behavior. Chat bots are thin adapters on top of the assistant.

### 3.8.4 Keeping answers grounded

Principle 2 says the AI may word a safety answer but never work it out. These safeguards keep that true even when the model doesn't follow its instructions.

**Which pet and which medication.**
- Safety tools take the pet and medication as the person said them ("Sonic", "his Cerenia", "the anti-nausea pill"). The core matches the words against names and aliases (02 §2.1) among the orders the caller may see.
- With one match, the answer names what was checked ("Sonic · Cerenia 16 mg"). With several, the core returns them and the assistant asks which ("Sonic's Cerenia or Biscuit's?"). With none, it says so, and the question goes to the owner (`AskOwner`).

**Times given in words.**
- A model never turns "Tuesday morning" or "at 6" into a date. It returns the words and the fields it read: a weekday, a part of the day, a clock time. The kernel resolves those against a reference date in the site's zone (`ResolveLocalTime`).
- In chat the reference is now. In care-note import it's the day the note was written, which the owner confirms.
- Parts of the day map to times the household sets; morning is 08:00 unless the owner changes it.
- Whatever a person confirms shows the weekday and date: "Not before Tue, Nov 10, 08:00". When more than one date fits, such as "Tuesday" in a note written on a Tuesday, the draft is flagged and the owner picks one (02 invariant 29).

**The answer line.**
- Code writes the facts. For each safety query (`CanAdminister`, `WhatsNext`, `Today`, and the last dose), a fixed template turns the result into one line in the reader's language, from the kernel's local fields: "Not yet. Sonic's Cerenia isn't allowed before Tue, Nov 10 at 8:00 am. Last dose: Sun, Nov 8 at 7:55 am." For a medication, the owner's instructions follow word for word. It's the same text the "Can I give it now?" button shows.
- The line always comes first and looks different: bold in the app, the first line of a text. The model writes only its own words, which follow the line ("Sorry he's sick again. If he keeps vomiting, call the vet.").

**Checking the model's words.**
1. Plain code scans the model's words for numbers (in digits or words), times and dates ("am", "noon", "tonight", "tomorrow", weekday and month names), dose words ("mg", "ml", "tablet", "click"), and a yes or no on giving a dose ("you can", "go ahead", "wait", "don't").
2. If it finds any, the model gets one rewrite and is told exactly what to drop: "Your words contain '8', 'tonight' and 'you can'. The answer line already gives the decision and the times."
3. The same check runs on the rewrite. If that fails too, the person gets the answer line alone.

- In the app and on the web, the answer line appears at once and the model's words follow once they pass, so a rewrite delays nothing that matters for safety. By text, a rewrite gets about 3 seconds, then one message goes out.
- A rewrite is another model call, metered like any other (§3.10).
- The check covers every reply in a turn that ran a safety query, and any message that names one of the household's medications. If the model answers about a medication without running the query, the core runs it from the names, or asks which one is meant.

**Measuring it.**
- Each check is stored with its message: passed, rewritten or dropped, and what it found. The first-try pass rate, and how often a rewrite fixes it, are AI quality measures beside the correction rate ([00 §0.8](00-product-offering.md#08-mvp-scope-and-success-measures)).
- A reply that fails twice in the same way is flagged for review, like a correction. The model may "believe" something the records don't say, such as an instruction given to the sitter in person.
- A word list misses some phrasings ("he'll be fine to have it"), which is why the line always comes first. Phrasings that slip through, found in testing or corrected by owners, are added to the list and to the test questions.
- **Test questions.** A fixed set of questions in many phrasings, SMS typos included, each with the tool, order and answer line it should produce. It runs whenever the model, the prompt or a template changes, and a change that picks the wrong pet or medication doesn't ship.

## 3.9 Deployment and placement

Decided (Q2): **cloud first, with the location of each part configurable.** Two rules make that possible:

1. **Each account's structured data has exactly one home.** The core, its database, search index and job workers run together: in the cloud for MVP, or on the owner's hardware in the home edition (V2, [08](08-home-and-cloud.md)). One account's records are never split across locations, so `CanAdminister` and `WhatsNext` give a sitter the same answer wherever they are.
2. **Anything behind a port can be placed independently.** Compute (language model, vision) and data the core only refers to (media files, encryption keys) can run in the cloud, on the owner's hardware, or nowhere (the null adapter), chosen per account.

### 3.9.1 What can run where

| Component | Connects through | Cloud | Owner's hardware |
|---|---|---|---|
| Core + database + search index + jobs | in process | MVP | V2: the home edition ([08](08-home-and-cloud.md)) |
| Language model, vision, speech-to-text | `LanguageModel`, `Vision`, `SpeechToText` ports | MVP (hosted, `normal` data only) | V2, via an edge node; may see `private` data |
| Media files | `BlobStore` port | MVP | V2, via an edge node, e.g. to keep prescription-label photos at home |
| Secret encryption keys | `Crypto` port | MVP (cloud KMS) | V2, via an edge node: the cloud stores ciphertext it can't decrypt |
| Notifications | `Notifier` port | MVP | Home edition: web push sent directly from home; native push through Pawsitter's push relay; SMS and email through the cloud messaging bridge ([08 §8.9](08-home-and-cloud.md#89-the-owner-away-from-home)). Standalone installs use web push, the owner's Discord bot, and email or SMS through the owner's own accounts ([08 §8.15](08-home-and-cloud.md#815-standalone-mode)) |
| Sign-in | `Identity` port | MVP | Home edition: the home core is the identity provider ([08 §8.5](08-home-and-cloud.md#85-identity-and-sign-in)) |
| Web app, mobile/PWA | public API | ✓ | ✓ |
| AI assistant, MCP server, chat bots | public API | ✓ | ✓, each with its own credential (§3.2) |

Interfaces can run anywhere that reaches the API; when each one ships is in [01 §1.9](01-features.md#19-interfaces-adapters-not-core).

### 3.9.2 The edge node

A small program the owner runs on their own machine (a home server, Mac mini or NAS). It:
- **dials out** to the cloud over an authenticated, encrypted connection, so the home network needs no port forwarding;
- is paired to one account with a one-time code, and offers only the capabilities the owner turns on (`language_model`, `vision`, `blob_store`, `crypto`);
- serves only those fixed operations. The cloud can't run arbitrary commands on the owner's machine;
- reports its health, so the core knows when a capability is offline.

In the core, a capability placed on an edge node is served by a `RemoteCapability` adapter that forwards the port call over that connection. Nothing else in the core knows where a port is implemented.

The home edition generalizes this connection into the **Home Link** ([08 §8.3](08-home-and-cloud.md#83-architecture)). Pawsitter's relay passes encrypted streams down it to the home core, which decrypts them itself, so the relay never sees their content. The same link carries push, messaging, certificate and update traffic, and still offers only fixed operations; SMS and email content and hosted-model prompts do pass through Pawsitter ([08 §8.14](08-home-and-cloud.md#814-what-each-companion-service-stores-and-sees)).

### 3.9.3 Routing by sensitivity

Each account has a routing table (stored in `Account.settings`): for each capability, an ordered list of providers, each with the highest sensitivity tier it may receive. The core uses the first provider that is healthy, allowed to see the request's data, and within the account's AI allotment (§3.10).

```yaml
# Example: an owner with a home server
language_model:
  - provider: edge:home-server/llama   # tried first: free, may see private data
    max_sensitivity: private
  - provider: hosted:claude            # fallback: metered, normal data only
    max_sensitivity: normal
vision:
  - provider: hosted:claude
    max_sensitivity: normal
blob_store:
  normal: cloud:s3
  private: edge:home-server/disk       # prescription-label photos stay home
crypto:
  default: cloud:kms                   # new secrets; each secret can override
```

Every port request is labeled with the highest sensitivity of the data it carries. If no allowed provider is available, the call returns `CapabilityUnavailable` with a reason (`offline`, `not_allowed` or `allotment_exhausted`), and the feature degrades: a visit report without prose, a placeholder instead of a photo. A request never falls through to a provider that isn't allowed to see its data; the caller may retry with the input redacted to a lower tier. The egress policy (04 §4.4) decides *what* may leave; the routing table decides *where* it goes.

### 3.9.4 Trade-off: parts at home can go offline

Anything placed at home is unavailable when that machine or the home internet is down. This matters most for secrets: a sitter at the front door can't reveal the lockbox code if its key is on a machine that lost power. So:
- New secrets default to the cloud KMS. Each secret records its `key_id`, so the owner can move individual keys home: the Wi-Fi password's key might live at home while the lockbox code, which a sitter needs at the door, stays in the cloud.
- Before an engagement starts, and while it's active, the core runs a **readiness check** on every capability the engagement depends on and warns the owner if one is offline.
- In the home edition every key is at home. Door codes a sitter needs at the door are staged on the sitter's phone when the access window opens, and backup reminders run from the cloud, so a dark house doesn't lock anyone out ([08 §8.10](08-home-and-cloud.md#810-outages-and-availability-at-home)).

### 3.9.5 Rules the core follows from day one

So that moving a part later is configuration, not a rewrite:
1. Capabilities are reached only through their ports. Adapters are chosen per account at runtime by a `CapabilityRouter`, not hard-wired at startup.
2. Port calls are asynchronous with timeouts, and every port can return `CapabilityUnavailable`. Features handle it by degrading.
3. Port inputs and outputs are plain, serializable data (no open files, sessions or callbacks), so every port except `Repository`/`UnitOfWork` can be forwarded over a network.
4. Every port request carries the sensitivity of its data.
5. References to media and keys are opaque and location-independent (`storage_key` and `key_id` include the provider), so moving a file between stores doesn't change domain records.
6. An interface's identity and egress tier come from its credential, never from what it claims (§3.2).
7. Records are sync-ready: client-generated UUIDv7 ids, a `version` on every row with every revision kept, `expected_version` on edits, idempotent commands with a `command_id`, and the event log as the replication stream. This keeps the home edition, moving between editions, and hybrid sync possible.

### 3.9.6 Shapes over time

| Shape | When | Structured data lives | Notes |
|---|---|---|---|
| Cloud | MVP | Cloud (Postgres, S3, KMS) | Hosted model on `normal` data. Interfaces can run anywhere. |
| Cloud + edge node | V2 | Cloud | The owner's hardware runs a local model and vision, and keeps private media and chosen secret keys. |
| Home edition | V2 (beta, then GA) | Owner's hardware (SQLite, local disk) | Connected: reached through Pawsitter's relay at its own HTTPS name, with companion services for push, messaging, AI, backups and updates. Standalone: no Pawsitter services, only what the owner sets up ([08](08-home-and-cloud.md)). |
| Hybrid sync | Later | Replicated between home and cloud through the event log | Only if there's real demand; the most complex shape. It would replace the one-data-home rule (02 invariant 27). |

## 3.10 AI usage metering

Hosted models are paid per token, so every account has an **AI allotment**, and the core meters each hosted model call against it. Metering is an ordinary core module: it doesn't depend on any provider, and the same ledger and limits meter SMS reminders to sitters, which are paid per message.

### 3.10.1 One gateway for every model call

Every model call goes through one core service, the `ModelGateway`, whether it comes from a core feature (a visit report) or the AI assistant (a chat reply). In the cloud, the core is the only component that holds provider API keys; home installs reach hosted models through Pawsitter's model proxy instead (§3.10.3). Interfaces never call a hosted model directly, so usage can't bypass metering, and a compromised chat bot can't run up a bill. Model generation isn't part of the public API, so the API can't be used as a general-purpose model proxy. The MCP server adds no model cost: MCP clients bring their own model and only call core tools.

Each call takes the same steps:

1. **Classify.** Find the highest sensitivity of the input (04 §4.4).
2. **Route.** List the providers allowed to see it, in the account's order (§3.9.3).
3. **Check and reserve.** For a billable provider, estimate the call's maximum use (input tokens plus the requested output limit), check it against the credit balance and every applicable limit, and reserve it atomically, so two family members chatting at once can't overspend. If a limit would be exceeded, apply its `on_exceed` rule: `degrade` tries the next provider (a cheaper model, or the owner's edge node), and `block` returns `CapabilityUnavailable(allotment_exhausted)` with the reset time.
4. **Call.** Cap output tokens at what the reservation covers.
5. **Settle.** Record actual usage from the provider's response, release the unused part of the reservation, and raise threshold events (80 %, 100 %) that notify the owner. If actual usage can't be read (a lost connection), settle at the reserved amount and let reconciliation correct it.

### 3.10.2 Tokens, cost, or both

Every call is recorded three ways: **raw tokens** (input, output, cache reads and writes, images), **provider cost** (what we pay, from a versioned price table) and **credits** (what the customer's allotment is measured in).

Credits come from per-model **credit rates**. Rates proportional to provider prices make credits cost-based; equal rates for every model make them token-based; anything in between is a blend. On top of the credit balance, an account can have any number of extra limits on raw tokens, cost or request counts, and a call must pass all of them. "500 credits a month, at most 50,000 tokens a day, no more than 20 requests a minute" is three limits.

| Limit field | Values |
|---|---|
| Metric | `credits` · `tokens` · `cost` · `requests` |
| Window | billing period · rolling (`P1D`, `PT1H`, `PT1M`) · one assistant turn (all calls sharing a `correlation_id`; stops runaway tool loops) |
| Scope | account · member · engagement (cap a sitter's use) · purpose (keep some allotment for visit reports) · integration |
| On exceed | `block` · `degrade` · `allow_overage` (later, billed) |
| Warn at | thresholds, e.g. 80 % and 100 % |

The plan sets the default limits. An owner can add tighter limits (cap a sitter at 20 % of the month) but never looser ones.

### 3.10.3 Who pays

Usage is charged to the account in the caller context: a sitter chatting about the Campbells' cat uses the Campbells' allotment, and SMS reminders sent to that sitter are charged to the Campbells too. Home installs reach hosted models through Pawsitter's model proxy, which holds the provider keys and is the metering authority; home cores never hold Pawsitter's keys ([08 §8.3](08-home-and-cloud.md#83-architecture)). The messaging bridge is the metering authority for SMS from home installs in the same way. Calls to the owner's edge node, and later to a provider key the owner brings, are recorded for the usage display but aren't billable.

### 3.10.4 Running out never affects care

Safety-critical answers (`CanAdminister`, `WhatsNext`, `Today`, `EmergencyCard`) are deterministic core queries and never touch a model (principle 2). When the allotment runs out, chat and generated prose pause, nothing else. Every interface keeps a non-AI path to those answers: the app shows the structured what's-next and medication cards, and bots fall back to plain commands.

## 3.11 Runtime and tech

Decided (Q13): **TypeScript compiled to plain JavaScript.** The full design is in [07](07-portable-core.md).

- **Kernel and services.** The kernel is one strict-mode script with ES2017 syntax and a JSON-string interface, `dispatch(op, requestJson)`. Core services are asynchronous and reach the outside world only through the ports, supplied as one host object.
- **Shims.** Hosts may supply capabilities: the clock, randomness, timers, logging, storage. They never supply anything that decides a result. Time-zone data, recurrence and exact decimals are bundled inside the kernel, because hosts' own time-zone data disagree today.
- **Hosts.** For MVP: Node on the cloud server, browsers and the owner-app shell; Node on the owner's machine comes with the home edition (V2). JavaScriptCore, Hermes, the AndroidX sandbox, Jint and ClearScript follow ([07 §7.10](07-portable-core.md#710-supported-hosts)).
- **API.** HTTP + JSON with an OpenAPI schema generated from the command and query schemas, so every client, the MCP tool list and native types (Swift, Kotlin, C#) come from one definition.
- **Tests.** One conformance corpus, compared byte for byte on every supported engine, plus property tests and differential oracles for time zones and recurrence ([07 §7.11](07-portable-core.md#711-proving-it-the-conformance-suite)).
