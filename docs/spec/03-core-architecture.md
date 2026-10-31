# 3. Core architecture

## 3.1 Shape: ports and adapters

```
            ┌──────────────────────── adapters (driving) ───────────────────────┐
            │  HTTP API · Web app · Mobile/PWA · CLI · AI assistant · MCP · bots │
            └───────────────────────────────┬───────────────────────────────────┘
                                            │ commands / queries (+ caller context)
                ┌───────────────────────────▼───────────────────────────┐
                │                         CORE                          │
                │  Application services: command & query handlers       │
                │  Policy: authorization, sensitivity, redaction        │
                │  Domain: entities, invariants, schedulers, safety     │
                │  rules (can_administer, whats_next), event creation   │
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
- **AI is an adapter on both sides.** As a *driving* adapter, the assistant turns natural language into core queries and commands. As a *driven* port (`LanguageModel`), the core may ask for prose (a visit-report summary), but never for a fact or a decision.

## 3.2 Caller context

Every command and query carries a `CallerContext`:

```
CallerContext {
  account_id
  actor: Actor            # user / system / integration, + on_behalf_of
  interface: "web" | "mobile" | "api" | "assistant" | "mcp" | "discord" | ...
  now: Instant            # from the Clock port at the edge, so a request is evaluated at one instant
  locale, request_id
}
```

The policy layer uses `actor` + `interface` to decide access and redaction. For example, the `assistant` interface never receives secret plaintext unless the secret allows it, and private photos are replaced by placeholders for adapters that leave the device.

## 3.3 Commands (writes)

Each command validates input, checks policy, enforces invariants, writes through the `UnitOfWork`, and emits events, all atomically. Commands are idempotent when given a client `command_id` (safe retries and offline sync).

| Area | Commands |
|---|---|
| Accounts & access | `CreateAccount`, `InviteMember`, `AcceptInvitation`, `ChangeMemberRole`, `RemoveMember`, `CreateEngagement`, `ConfirmEngagement`, `CancelEngagement`, `PlanVisits`, `CheckIn`, `CheckOut` |
| Sites & places | `CreateSite`, `UpdateSite`, `CreatePlace`, `MovePlace` (re-parent), `RenamePlace`, `ArchivePlace` |
| Pets | `CreatePet`, `UpdatePet`, `RecordPetLocation`, `RecordWeight` |
| Items | `CreateItem`, `UpdateItem`, `SetHomePlace`, `MoveItem`, `RecordSighting`, `ReturnItemHome`, `ArchiveItem` |
| Inventory | `Restock`, `RecordConsumption`, `CountStock`, `TransferStock`, `SetStockThresholds`, `AddToShoppingList`, `MarkBought` |
| Medications | `CreateMedicationOrder`, `ReviseMedicationOrder`, `SetNotBefore`, `PauseOrder`, `DiscontinueOrder`, `RecordAdministration`, `OverrideAndRecordAdministration` |
| Care | `CreateRoutine`, `UpdateRoutine`, `PauseRoutine`, `CompleteTask`, `SkipTask`, `SnoozeTask`, `UndoTaskCompletion` (time-limited) |
| Knowledge | `CreateKnowledgeEntry`, `ReviseKnowledgeEntry`, `ArchiveKnowledgeEntry`, `CreateSecret`, `RotateSecret`, `RevealSecret` (a command, because it's logged) |
| Contacts | `CreateContact`, `UpdateContact`, `LinkContact`, `UnlinkContact` |
| Media | `BeginUpload` → `CompleteUpload` (strips metadata, makes variants), `LinkMedia`, `UnlinkMedia` |
| Incidents | `ReportIncident`, `AcknowledgeIncident`, `ResolveIncident` |

## 3.4 Queries (reads)

Queries return structured, typed results, ready for any adapter to render. The safety-relevant ones are deterministic and explain themselves.

| Query | Returns |
|---|---|
| `WhatsNext(scope = site / pet / engagement)` | Overdue tasks first, then the next due task, each with routine, pet, window and instructions. |
| `Today(scope)` | All of today's tasks (in the site's local day) with status. |
| `CanAdminister(order_id)` | `{allowed, reason, next_allowed_at, last_given_at, doses_in_window, instructions_verbatim}` |
| `MedicationSummary(pet_id)` | Active orders with last dose, next due and remaining stock. |
| `WhereIs(query)` | Ranked matches across pets, items, places and aliases: current placement, home place, path ("Home › Kitchen › Pantry › Shelf 2"), last seen time, photos. |
| `WhatsIn(place_id, recursive)` | Items, stock and pets at a place or subtree. |
| `PlaceTree(site_id)` | The nested place hierarchy. |
| `LowStock(scope)`, `ShoppingList()` | |
| `KnowledgeFor(subject_id, include_related)` | Entries (critical first), playbooks, linked contacts. |
| `EmergencyCard(pet_id / site_id)` | Vets, emergency vet, owner contacts, critical notes, active medications. Fits on one screen. |
| `Activity(scope, range)`, `VisitReport(visit_id)` | Events grouped for display. |
| `Search(text, filters)` | Full-text across names, aliases and knowledge, via the `SearchIndex` port. |
| `Context(scope, budget)` | **A compact, permission-filtered snapshot for assistant adapters**: the current time in the site's zone, pets, today's tasks with status, active medications with `CanAdminister` results, relevant knowledge. This is the generalized "send everything in the prompt" from the prototype. |

## 3.5 Events

Every command emits one or more events (`2.12 Event`), stored in the same transaction (transactional outbox) and then published through `EventPublisher`. Consumers are adapters or core jobs:
- the **notifier** (task reminders, overdue escalation, low stock, urgent incidents, engagement starting)
- **visit-report** assembly
- the **search index** updater
- **sync** to offline clients
- analytics, webhooks and integrations (later)

## 3.6 Background jobs (`JobScheduler` port)

| Job | Purpose |
|---|---|
| `MaterializeTasks` | Keep calendar tasks generated N days ahead; regenerate when routines change. |
| `TaskStatusSweeper` | Mark `missed`, send reminders and escalations. Reads are correct without it; it exists for notifications. |
| `EngagementLifecycle` | Open/close caregiver access at window edges; activate engagement-only routines. |
| `LowStockCheck` | Raise `stock.low` and fill the shopping list. |
| `MediaPipeline` | Strip metadata, make variants, compute hashes. |
| `Retention` | Hard-delete soft-deleted data past retention; purge secrets of closed engagements from caches. |

## 3.7 Ports

| Port | Responsibility | Example adapters |
|---|---|---|
| `Repository<T>` / `UnitOfWork` | Load/save aggregates; transactions; tenant scoping built in | Postgres (cloud), SQLite (local/self-hosted, tests) |
| `Clock` | `now()` | System clock; fixed clock in tests |
| `IdGenerator` | UUIDv7 | |
| `BlobStore` | Put/get/delete media; signed URLs | S3-compatible, local disk |
| `Crypto` | Envelope encryption for secrets; key rotation | Cloud KMS, local keyfile |
| `Identity` | Verify sign-in, map to `User` | OIDC, passkeys, magic links |
| `Notifier` | Deliver a message to a user on a channel | Push (APNs/FCM), email, SMS, Discord, Slack |
| `EventPublisher` | Publish committed events | In-process bus, queue, webhooks |
| `JobScheduler` | Run recurring and one-off jobs | Cron in-process, queue workers |
| `SearchIndex` | Full-text + fuzzy name/alias search | SQLite FTS5, Postgres full-text, Meilisearch |
| `Geo` | Geocode addresses; geofence checks | Mapping provider, none |
| `LanguageModel` | Generate prose from structured input (reports, summaries) | Local llama.cpp, Claude API, none |
| `Vision` | Describe or identify a photo ("which item is this?") | Local VLM, hosted model, none |
| `BarcodeLookup` | Barcode → product details | Product databases, none |

Every port has a **null implementation**, so the core runs fully without AI, search engines, maps or notifications. Features degrade gracefully instead of failing.

## 3.8 How the AI assistant plugs in

The assistant is a driving adapter with this loop:

1. Build a prompt from `Context(scope, budget)`: compact, current, permission-filtered.
2. Expose core **queries and commands as tools** (`whats_next`, `can_administer`, `where_is`, `complete_task`, `record_administration`, `report_incident`…), each a thin wrapper running with the user's `CallerContext` (`interface = "assistant"`, `on_behalf_of = user`).
3. The model chooses tools and phrases results. **Facts come only from tool results**: doses and times are quoted from `CanAdminister` and `instructions_verbatim`, never computed by the model.
4. Writes requested through the assistant ("I gave him his pill") go through the same commands, so they're validated, safety-checked and logged as *assistant on behalf of Jane*.

The **MCP server** is the same tool set exposed over MCP, so any MCP-capable client gets exactly the same safe behavior. Chat bots are thin adapters on top of the assistant.

## 3.9 Deployment shapes

The same core runs in several shapes. Which to lead with is an open question.

| Shape | Storage | Notes |
|---|---|---|
| **Cloud (SaaS)** | Postgres + S3 + KMS | Multi-tenant; mobile apps; push notifications; easiest for sitters. |
| **Self-hosted / local-first** | SQLite + local disk + local LLM | The prototype's privacy story: nothing leaves the home. Single account. |
| **Hybrid** | Local node syncs selected data to the cloud | Owner keeps secrets and medical data local; caregivers get time-boxed synced access. Most complex. |

Design for sync from day one, even if it ships later: client-generated UUIDv7 ids, `version` on every row, idempotent commands with `command_id`, and the event log as the replication stream.

## 3.10 Suggested tech (to confirm)

- **Core:** Python 3.12+ with typed dataclasses / Pydantic for the domain and a hand-written repository layer (SQLAlchemy Core), to reuse prototype knowledge. TypeScript end to end is the alternative if the web/mobile apps lead. See open questions.
- **API:** HTTP + JSON with an OpenAPI schema generated from command/query types, so every client and the MCP tool list are generated from one definition.
- **Tests:** property tests for recurrence/DST and `can_administer`; a fixed `Clock` everywhere.
