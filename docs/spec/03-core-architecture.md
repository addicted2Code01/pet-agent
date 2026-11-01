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
  egress_tier: "normal" | "private"   # the most sensitive data this interface may receive
  now: Instant            # from the Clock port at the edge, so a request is evaluated at one instant
  locale, request_id
}
```

`interface` and `egress_tier` come from the authenticated credential, never from the request. First-party apps get `private` (what a user may see is still decided by their role). The owner registers each other integration, for example an MCP server on their laptop with a local model, and sets its tier; the default is `normal`.

The policy layer uses `actor`, `interface` and `egress_tier` to decide access and redaction. For example, the `assistant` interface never receives secret plaintext unless the secret allows it, and private photos are replaced by placeholders for interfaces with a `normal` tier.

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
| AI usage | `SetUsageLimit`, `RemoveUsageLimit`, `GrantCredits` (admin), `PurchaseCredits` (V2) |
| Placement | `PairEdgeNode`, `UnpairEdgeNode`, `SetCapabilityRoutes`, `MoveSecretKey` (all V2) |

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
| `AiUsage(scope, period)` | Used and remaining for the credit balance and each limit; breakdown by member, purpose and model; reset time; projected run-out date. |
| `Readiness(engagement_id)` | Whether every capability the engagement depends on (secret keys, media, model) is reachable (§3.9.4). |
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
| `PeriodRollover` | Start each billing period: issue the plan's credit grant and expire the previous one. |
| `ReservationSweeper` | Release usage reservations whose calls never settled (crashed workers). |
| `UsageReconciliation` | Compare the usage ledger with providers' usage reports daily; flag drift. |
| `CapabilityHealth` | Check edge nodes and providers; run engagement readiness checks and warn owners (V2). |

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

Any port except `Repository`/`UnitOfWork` can also be served by a `RemoteCapability` adapter that forwards calls to the owner's edge node (§3.9.2). `LanguageModel` and `Vision` are only ever called through the `ModelGateway`, which routes and meters them (§3.10).

## 3.8 How the AI assistant plugs in

The assistant is a driving adapter with this loop:

1. Build a prompt from `Context(scope, budget)`: compact, current, permission-filtered.
2. Expose core **queries and commands as tools** (`whats_next`, `can_administer`, `where_is`, `complete_task`, `record_administration`, `report_incident`…), each a thin wrapper running with the user's `CallerContext` (`interface = "assistant"`, `on_behalf_of = user`).
3. The model chooses tools and phrases results. **Facts come only from tool results**: doses and times are quoted from `CanAdminister` and `instructions_verbatim`, never computed by the model.
4. Writes requested through the assistant ("I gave him his pill") go through the same commands, so they're validated, safety-checked and logged as *assistant on behalf of Jane*.
5. The assistant's own model calls go through the `ModelGateway` (§3.10), so they're routed by sensitivity and metered against the account's allotment.

An assistant the owner runs on their own hardware with a local model is just another interface with its own credential: it calls the public API like any other client, and the gateway and metering don't apply.

The **MCP server** is the same tool set exposed over MCP, so any MCP-capable client gets exactly the same safe behavior. Chat bots are thin adapters on top of the assistant.

## 3.9 Deployment and placement

Decided (Q2): **cloud first, with the location of each part configurable.** Two rules make that possible:

1. **Each account's structured data has exactly one home.** The core, its database, search index and job workers run together: in the cloud for MVP, or on the owner's hardware in a later self-hosted edition. One account's records are never split across locations, so `CanAdminister` and `WhatsNext` give a sitter the same answer wherever they are.
2. **Anything behind a port can be placed independently.** Compute (language model, vision) and data the core only refers to (media files, encryption keys) can run in the cloud, on the owner's hardware, or nowhere (the null adapter), chosen per account.

### 3.9.1 What can run where

| Component | Connects through | Cloud | Owner's hardware |
|---|---|---|---|
| Core + database + search index + jobs | in process | MVP | Later (self-hosted edition) |
| Language model, vision | `LanguageModel`, `Vision` ports | MVP (hosted, `normal` data only) | V2, via an edge node; may see `private` data |
| Media files | `BlobStore` port | MVP | V2, via an edge node, e.g. to keep prescription-label photos at home |
| Secret encryption keys | `Crypto` port | MVP (cloud KMS) | V2, via an edge node: the cloud stores ciphertext it can't decrypt |
| Notifications | `Notifier` port | MVP | No: push must go through Apple/Google, email and SMS through providers |
| Sign-in | `Identity` port | MVP | Self-hosted edition only |
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

The self-hosted edition later uses the same connection in reverse: a cloud relay forwards sitters' API calls to the home core, and the home core sends push notifications through the cloud.

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

### 3.9.5 Rules the core follows from day one

So that moving a part later is configuration, not a rewrite:
1. Capabilities are reached only through their ports. Adapters are chosen per account at runtime by a `CapabilityRouter`, not hard-wired at startup.
2. Port calls are asynchronous with timeouts, and every port can return `CapabilityUnavailable`. Features handle it by degrading.
3. Port inputs and outputs are plain, serializable data (no open files, sessions or callbacks), so every port except `Repository`/`UnitOfWork` can be forwarded over a network.
4. Every port request carries the sensitivity of its data.
5. References to media and keys are opaque and location-independent (`storage_key` and `key_id` include the provider), so moving a file between stores doesn't change domain records.
6. An interface's identity and egress tier come from its credential, never from what it claims (§3.2).
7. Records are sync-ready: client-generated UUIDv7 ids, a `version` on every row, idempotent commands with a `command_id`, and the event log as the replication stream. This keeps the self-hosted edition and hybrid sync possible.

### 3.9.6 Shapes over time

| Shape | When | Structured data lives | Notes |
|---|---|---|---|
| Cloud | MVP | Cloud (Postgres, S3, KMS) | Hosted model on `normal` data. Interfaces can run anywhere. |
| Cloud + edge node | V2 | Cloud | The owner's hardware runs a local model and vision, and keeps private media and chosen secret keys. |
| Self-hosted | Later | Owner's hardware (SQLite or Postgres, local disk) | A cloud relay gives sitters remote access and delivers push notifications. |
| Hybrid sync | Later | Replicated between home and cloud through the event log | Only if there's real demand; the most complex shape. |

## 3.10 AI usage metering

Hosted models are paid per token, so every account has an **AI allotment**, and the core meters each hosted model call against it. Metering is an ordinary core module: it doesn't depend on any provider, and the same mechanism can later meter other paid capabilities such as SMS.

### 3.10.1 One gateway for every model call

Every model call goes through one core service, the `ModelGateway`, whether it comes from a core feature (a visit report) or the AI assistant (a chat reply). The core is the only component that holds provider API keys. Interfaces never call a hosted model directly, so usage can't bypass metering, and a compromised chat bot can't run up a bill. Model generation isn't part of the public API, so the API can't be used as a general-purpose model proxy. The MCP server adds no model cost: MCP clients bring their own model and only call core tools.

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

Usage is charged to the account in the caller context: a sitter chatting about the Campbells' cat uses the Campbells' allotment. Calls to the owner's edge node, and later to a provider key the owner brings, are recorded for the usage display but aren't billable.

### 3.10.4 Running out never affects care

Safety-critical answers (`CanAdminister`, `WhatsNext`, `Today`, `EmergencyCard`) are deterministic core queries and never touch a model (principle 2). When the allotment runs out, chat and generated prose pause, nothing else. Every interface keeps a non-AI path to those answers: the app shows the structured what's-next and medication cards, and bots fall back to plain commands.

## 3.11 Suggested tech (to confirm)

- **Core:** Python 3.12+ with typed dataclasses / Pydantic for the domain and a hand-written repository layer (SQLAlchemy Core), to reuse prototype knowledge. TypeScript end to end is the alternative if the web/mobile apps lead. See open questions.
- **API:** HTTP + JSON with an OpenAPI schema generated from command/query types, so every client and the MCP tool list are generated from one definition.
- **Tests:** property tests for recurrence/DST and `can_administer`; a fixed `Clock` everywhere.
