# 8. Home and cloud editions

One codebase runs in two ways: as a hosted service (**cloud**), or on the owner's own always-on computer or NAS (**home**). In both, a sitter gets set up by scanning a QR code.

How this was decided, on 2026-11-04:
- Four research areas (HTTPS on a home network, sign-in and pairing, remote access and push, packaging) were fact-checked: 142 checks, with 77 confirmed, 22 corrected and 43 unverifiable. Most unverifiable ones match known facts but weren't re-read, so they're listed as hypotheses in §8.18.
- Three independent designs were then written (simplicity first, unified experience first, security first). A judge scored them, picked "unified experience" (22 points, against 21 and 20) and grafted in 23 ideas from the other two.
- A red-team review followed, and its fixes are built in below.

## 8.1 The decisions

1. **One TypeScript codebase, two composition roots.** *Cloud* is multi-tenant: Postgres, S3, KMS. *Home* serves one household from an always-on Mac, Windows PC or NAS: SQLite, local disk, a local key. Each account's data lives in exactly one of them (README principle 8).
2. **Home is relay-first.** Every home install gets its own HTTPS name. Pawsitter's relay passes encrypted traffic through to it without decrypting, so the same address works on the home Wi-Fi, guest Wi-Fi, mobile data and abroad, with no port forwarding (§8.4).
3. **One QR join for both editions.** A code that's sent, shown on a screen or printed opens the same join flow. A second factor binds it to the right person (§8.7).
4. **Every sitter is a real, lightweight user.** No password, no app and no sign-up form, but their own identity, with access bounded by the trip and revocable at once.
   - Cloud sitters have one login across every household they sit for.
   - Home sitters are local to the install, and can link a Pawsitter account (§8.5).
   - This replaces the no-account sitter link (Q11).
5. **Home owners choose their sign-in options from a menu** with a recommended default (§8.6).
6. **Companion services hold routing data or ciphertext, never care records.** These are the relay, DNS and certificates, push relay, messaging bridge, model proxy, watchdog and updates. The one declared exception is a discreet reminder schedule that keeps medication reminders going if the home goes dark (§8.10).

**Why not just serve plain HTTP on the home network?**
- An address like `http://192.168.1.20` isn't a secure context. Browsers then give no passkeys, no service worker (so no offline copy and no web push), no camera, no `crypto.subtle` and no `Secure` cookies. All of this was checked in Chrome 153.
- Self-signed certificates don't help: browsers refuse passkeys and service workers on pages with certificate errors, and asking every sitter to trust a private certificate authority on their iPhone isn't realistic.
- Guest Wi-Fi often isolates guests from the home network.
- A server that only works inside the home can't reach the owner while they're away on the trip.

## 8.2 What each edition promises

| Situation | Cloud | Home |
|---|---|---|
| Where household data lives | Pawsitter's cloud | The owner's computer or NAS |
| Owner away on the trip | Works anywhere | Works anywhere, through the relay |
| Sitter on mobile data or guest Wi-Fi | Works | Works, through the relay |
| Home internet down | Unaffected | Offline copy, printed care sheet, cloud backup reminders, door codes staged on the sitter's phone (§8.10) |
| Pawsitter's cloud down | Down | The home itself keeps running; remote access, SMS and native push stop |
| Host computer asleep or off | n/a | Like an internet outage; the watchdog alerts the owner |
| Owner needs a Pawsitter account | Yes | Yes for a connected install (pairing, relay, alerts, billing); the data stays home |
| Owner's effort | None | An always-on machine; certificates, updates and backups are automatic |

The home edition keeps data **at rest** at home. It still relies on Pawsitter for the relay, DNS, certificates, SMS and push. Setup says so plainly, with this table.

## 8.3 Architecture

**Shared:**
- the kernel and core services ([07](07-portable-core.md));
- contracts: command, query and event schemas, OpenAPI, and the Home Link protocol;
- sign-in (passkeys, device sessions, joins, codes, step-up);
- crypto, the HTTP adapter, the web app;
- the Web Push sender, the native owner shells, and the test kit.

**Cloud only:**
- the Postgres store and the cloud composition root, which includes Pawsitter ID (the user directory) and the join routes;
- the companion services: the Home Link hub, the relay, DNS and certificates, the push relay, the messaging bridge and the model proxy.

**Home only:**
- the SQLite store (Node's built-in `node:sqlite`, which Bun also implements);
- the home composition root and the Home Link client;
- the notifier that sends through the companion services;
- the tray app and the installers.

**Nothing in the kernel or services knows which edition it's in.** An edition is only a choice of adapters at the composition root, plus `CallerContext.transport` (`loopback`, `lan`, `relay` or `cloud`). One contract and end-to-end suite runs against both compositions.

**Home topology.** The home core runs under a dedicated OS user and holds the kernel, services, SQLite database, media, keys, jobs and the web app.
- Listeners:
  - `localhost`, for the setup and recovery console only;
  - no inbound ports from the internet;
  - an optional LAN listener (§8.4) that checks every `Host` header against the install's names.
- One outbound **Home Link**, mutual TLS with a certificate from Pawsitter's private CA, issued at pairing. It carries:
  - relayed TLS streams, which the home core decrypts itself;
  - calls to the companion services;
  - inbound messages from the bridge;
  - scoped DNS writes for certificates;
  - heartbeats;
  - lock, revocation and data-update events.
- Web Push and certificate renewals go straight out over HTTPS. A local model runtime, if any, is reached on `localhost`.
- The same program can also run as the V2 edge node of a cloud account ([03 §3.9.2](03-core-architecture.md#392-the-edge-node)). In that case it offers capabilities only and holds no records.

**Cloud topology.** `app.<saas-domain>` runs the same server image with the cloud adapters, plus:
- **Pawsitter ID:** global users, passkeys, and an OIDC provider for linked home installs.
- **The join routes** `/j`, `/w` and `/h`, with a small routing table that maps each join to its account's address and holds no household fields.
- **The companion services,** which can be deployed separately.

## 8.4 HTTPS for home installs

- **The home zone.** A dedicated domain, separate from the cloud domain and held long-term. Passkeys and printed cards depend on it never changing.
  - Each install gets a random label: `https://<id>.<home-zone>`. Random, because every certificate is published in Certificate Transparency logs.
  - The zone is listed in the Public Suffix List, so installs are isolated from one another as separate sites. Without that listing, one install could set cookies on every other.
  - Until the listing ships in current Chrome, Safari and Firefox, the beta runs on a separate, invite-only zone.
- **Certificates.** The home core generates its own key and sends only a certificate request; the private key never leaves home. One certificate covers the name and its subdomains, validated through a DNS API scoped to that install.
  - CAs: Let's Encrypt is primary. A backup CA is reached through a Pawsitter-run ACME proxy, so no shared CA account key is ever stored on installs.
  - Renewal: through ACME Renewal Information, and again at startup, because a machine may be off for weeks.
  - Lifetimes are shrinking: 200 days now, 100 days from March 2027, and Let's Encrypt is moving to 64 and then 45 days.
  - Rate limits: until a rate-limit exemption or the Public Suffix List entry arrives, Let's Encrypt issues only 50 new certificates per registered domain per week. Installs keep their key and certificate across reinstalls.
  - DNS: CAA records name both CAs.
  - Transport: home cores never advertise HTTP/3, because the relay carries TCP only.
- **Trust, stated plainly.** Pawsitter controls the zone's DNS and so could obtain a certificate for any install. Keys never leave home, and owners can audit issuance in the public CT logs.
- **LAN paths** (all optional):
  - *Desktop LAN shortcut* (home GA): a stable `lan` name under the install, under a random label, that points at the machine's LAN address and is updated when DHCP changes. Some routers and DNS filters drop answers that point at private addresses; the tray app detects that and falls back to the relay.
  - *Split DNS* (power users): point the install's name at the LAN address in the router.
  - *Console* on the host itself (`http://localhost`): setup and recovery only.
- **No plain-HTTP mode for sitters.** "Basic LAN mode" was considered and dropped. It conflicts with the rule that medical data needs HTTPS ([07 §7.12](07-portable-core.md#712-open-items)), and its cookies leak to every other service on the same host. It also doesn't help in an outage, because the sitter needs it set up in advance on a second address. The outage plan is §8.10.
- **Hygiene.**
  - The home core accepts only its own `__Host-` cookies.
  - Every write checks `Origin`.
  - Every listener checks `Host`, which blocks DNS-rebinding attacks.
  - The client address comes from the relay stream, never from headers.

## 8.5 Identity and sign-in

- **Every person is a User.** A sitter becomes a *lightweight* user at join: a name from the invite, plus a contact verified by a code or a device approved by the owner. They have no password and can add a passkey later. Every action is attributed to a person and a device, and can be revoked per person or per device.
- **Cloud: Pawsitter ID.**
  - Users are global, with passkeys on the cloud domain, so one passkey works for every household. Fallback: a one-time code, or a magic link that signs in only after a tap, because mail scanners open links. Optional Sign in with Apple or Google.
  - Browser sessions: opaque ids in `__Host-` cookies.
  - Native shells and API clients: OAuth 2.1 with short-lived access tokens and rotating refresh tokens.
- **Per-account device grants (cloud).** A **Device** is one browser or app instance of one user. A **DeviceGrant** gives that device access to one account, with its role, engagement window and step-up state.
  - A join, code or approval in household A creates a grant for A only.
  - Using the same device in household B needs the user's own strong sign-in plus B's policy.
  - Step-up is scoped per device and per account, so verifying in A never unlocks B's door codes.
  - Revoking a device in A removes only A's grant. Owners see only the devices that hold a grant in their account.
- **Home: the home core is the identity provider.**
  - Users are local to the install, with passkeys on the install's name.
  - A person can link a Pawsitter account through OIDC; the home core stays the authority for membership and revocation.
  - A Pawsitter account that's disabled is pushed down the Home Link and applied on receipt.
  - One install hosts one account.
- **Caller context.** `CallerContext` gains:
  - `transport`: `loopback`, `lan`, `relay` or `cloud`;
  - `device_id`;
  - `auth_strength`: `passkey_uv`, `otp_verified`, `approved`, `pin` or `session`.

  All three come from the connection and the credential, never from the request. Transport is recorded for audit and never raises trust, and relayed traffic is never treated as local.
- **Step-up for door codes and medication-order changes.** Either of these, both scoped per device and account:
  - a passkey with user verification within 5 minutes;
  - a code verified within 24 hours ([04 §4.2](04-permissions-privacy.md#42-time-boxed-access)).

  Inside the home with no internet, a personal PIN or live owner approval works instead. Secrets are never served over plain HTTP, and recovery codes never count as a step-up.

## 8.6 Home sign-in options

Sign-in is always on, but nobody types a password. People join once by QR, and the owner chooses how strict each step is.

| Option | How it works | Revoking | Works with no internet | Default |
|---|---|---|---|---|
| **Paired devices** | Each phone or computer joins once by QR and keeps a device session (an `HttpOnly` cookie on the install's name). Caregiver sessions end with the trip. | Revoke the device or remove the person; the next request is refused | Only with split DNS (the name needs DNS) | **Sitters and family** |
| **Passkeys** on the install's name | Checked by the home core itself. Synced by iCloud Keychain and Google Password Manager; works across the relay name and the LAN shortcut. | Delete the passkey and its sessions | Only with split DNS | **Owners and admins**, with a printed recovery kit; offered to everyone |
| **One-time code** to a contact the owner entered | 6 digits, 10 minutes, 5 tries, sent by SMS or email through the bridge, only to a number or address the owner typed | Codes expire; changing the contact cancels pending ones | No | **The join check for sitters** with a contact on file; the online step-up for door codes |
| **Owner approval** | The joining device shows match words; an owner approves inside the Pawsitter app, seeing the person, device, time, approximate location and network | Deny, or revoke later | On the LAN path | **Card joins**, sitters with no contact on file, new owner devices |
| **Personal PIN** | 6 to 8 digits, set by a paired person, bound to that device; re-unlocks the app and serves as the offline step-up | An owner or the trip's approver resets it | Yes | **On** as the offline step-up |
| **Pawsitter account** (OIDC) | Sign in with an existing Pawsitter account; the owner still approves the first device | Remove the person locally; a cloud-side disable arrives as an event | No | Off; for sitters who use Pawsitter elsewhere |
| **Console** (`http://localhost`) | On the host only, behind the OS login plus a console token | Rotate the token | Yes | **Always on**, for setup and recovery |
| **Kiosk device** | A paired tablet shows Today, what's next and the emergency card. It can tick non-medication tasks, and can never record a dose, reveal a code or show private data. | Revoke the kiosk | On the LAN path | Off |
| Trusted home Wi-Fi (no sign-in) | Anyone on the home network sees a read-only Today view | Change the Wi-Fi password | Yes | **Not recommended; not offered in the beta.** The LAN is not a trust boundary, and the kiosk covers the need. |
| Shared household PIN | One PIN unlocks a person picker | Change the PIN for everyone | Yes | **Not recommended; not offered in the beta.** No per-person attribution or revocation. |

**Recommended default**, preselected at setup:
- **Owners and admins:** a passkey, a printed recovery kit (also saved to a password manager), and a second owner where possible. New owner devices need another owner's approval or a recovery code, and every owner is alerted.
- **Family:** a QR join approved by an owner.
- **Sitters:**
  - A QR join that becomes a paired device ending with the trip.
  - The join check is a code to the contact the owner entered. With no contact on file, or a printed-card join, the owner approves instead. At a displayed QR, the owner approves on the spot.
  - A passkey is offered, never required.

**The beta ships one preset:** passkeys for owners, paired devices plus a code for sitters, and a PIN for the offline step-up. The kiosk and Pawsitter-account sign-in arrive at GA. The two no-login options aren't offered.

## 8.7 Joining by QR

**Rules for every join, in both editions:**
- **The link.** Every QR opens a link on Pawsitter's join domain, which redirects (a top-level navigation, never a background request) to the account's own address: the cloud, or the home install.
- **The secret.** It's only in the URL fragment (`#…`), so it never reaches server logs, `Referer` headers or link previews. Opening the page consumes nothing; the secret is claimed by a POST after the person taps Continue.
- **What the page reveals.** Until the second factor passes, only "Invite for <name> from <owner's first name>": no dates and no address, which would reveal an empty house.
- **The second factor is tied to this browser.** It's a code sent to the contact the owner entered, or the owner's approval. The confirming link works only in the browser that started the request. Anywhere else, it says "this request started on another device". A typed code is the fallback.
- **The SMS wording:** "Pawsitter code to add a device for <household>. Only enter it at <domain>."
- **In-app browsers.** Gmail and similar apps open links in their own browser, with its own cookies. After joining there, the page offers a one-time link to continue in the phone's real browser. On iPhone it also offers Add to Home Screen, which web push needs, and continues the session inside the installed app.
- **The owner sees every join:** "Claimed by Jamie's iPhone, Safari, 18:02", with Revoke. Reusing a spent link alerts the owner and names the device.

| | Sent invite | Displayed join window | Printed home card |
|---|---|---|---|
| **What it is** | A link (and its QR, shown on the owner's own screen) sent by message, SMS or email | A QR plus a short code, shown on the owner's phone, the tray app or a kiosk | A card on the fridge or the care sheet: a QR, the plain domain and a short household code to type |
| **Secret** | 256 random bits, single use; the owner can resend, which rotates it | 128-bit nonce, rotating every 30 seconds (each lives at most 60 seconds), plus a 6-character code valid 2 minutes | None. The card holds a random locator that grants nothing on its own and can be rotated or disabled. |
| **Valid** | Until the trip's access ends; a sitter can join early, and their session doesn't idle out before the trip | While the window is open (10 minutes by default; the owner can lengthen it) | Only while a trip's access window is open (from 24 hours before) or the owner has opened a join window |
| **Second factor** | A code to the contact the owner entered, or owner approval | The owner approves on the spot; at an unattended kiosk, the trip's join check | The person's name plus the contact the owner registered, then a code; or owner approval with match words |
| **Devices** | Two by default (a phone and a tablet), with owner alerts | First join closes the window | One per request |
| **Limits** | 5 failed claims lock the invite and alert the owner | 5 code attempts per window | 5 requests an hour and 20 a day per card; owner alerted on every request; identical responses, so nobody can probe which contacts exist |

**Recovering a spent or lost invite.** The verified contact can re-claim on a new device with a fresh code; this replaces the old device. Locked invites and trip codes can be reset by the owner or the trip's named approver (§8.12).

**Linking a home server** (setup):
1. The installer starts the server on `localhost` only, with a single-use setup secret.
2. In the Pawsitter app, the owner taps "Link a home server", which creates a 10-minute claim code.
3. The owner types that code on the local setup page. Container installs take it from an environment variable or an admin command, and never print secrets to logs.
4. Both screens show the server's name and key fingerprint. Once the owner confirms, the hub issues the Home Link certificate and the install's name, and every owner is alerted.

The trusted side always creates the code, and the owner types it into the box, so the device-code phishing seen in real attacks doesn't apply.

**Adding an owner or family device.** Use a synced passkey or the browser's cross-device passkey sign-in. Without a passkey, a signed-in device shows a 2-minute QR and code, and confirms the new device's details and match words. Every other owner gets a "this wasn't me" alert.

**Accessibility.** The join, approval, step-up, kiosk and console flows meet WCAG 2.2 AA:
- typeable codes beside every QR;
- one code field with one-time-code autofill and paste;
- "send a new code" without penalty, and windows the owner can lengthen;
- spoken instructions and alt text;
- texts localized to the recipient's language;
- testing with VoiceOver and TalkBack before the beta.

## 8.8 Revocation, ending and late doses

- **Immediate.** `authorize()` reads the membership, engagement, device grant and session on every request, so revoking never waits for a token to expire. This holds in both editions, because every request ends at the account's data home.
- **Owner actions:**
  - revoke one device;
  - suspend or remove a person;
  - cancel or end a trip ("I'm home"), which ends every caregiver device on it;
  - revoke an invite, rotate a trip code or a printed card;
  - sign out everywhere;
  - at home, lock remote access.
- **What revoking does.** Everything happens in one transaction, with revisions and events:
  - live streams close;
  - push subscriptions and native push bindings are removed;
  - deleted passkeys are hidden in Chrome and Safari password managers through the WebAuthn Signal API.
- **Ended is not revoked.** A trip ending must never lose a dose.
  - The phone's outbox of unsent doses and task completions is never wiped by a refused request; only the read cache is.
  - An *ended* caregiver device keeps an upload-only grant for 7 days. It can still send administrations and completions whose device time falls inside the access window. They're flagged late-synced, and the owner is alerted at once.
  - A *revoked* device gets one quarantined upload, which the owner reviews.
  - Before closing, "I'm home" warns: "Jamie's phone last synced 19:40 and may have unsent entries". The sitter sees "N entries not sent", with an SMS fallback.
  - An ended device can still read the sitter's own events and the stay summary ([04 §4.2](04-permissions-privacy.md#42-time-boxed-access)).
- **The offline copy after revoking.**
  - It's encrypted under a key the server leases to the device for 24 to 48 hours and renews while online, so a revoked device loses access when the lease lapses.
  - It refuses to open if the device clock is earlier than the last server time it saw.
  - It holds tasks only 48 hours ahead, not the whole stay.
  - The revoke dialog says plainly that revoking can't erase what's already on the phone, and suggests rotating any code that was revealed.
- **At home:**
  - Revoking works locally even when Pawsitter's cloud is down.
  - From the Pawsitter account, an owner can send a signed "revoke this device" command down the Home Link. If the house is unreachable, they can instead lock remote access, which tells the relay to stop routing the install. Both need a passkey step-up and alert every owner.

## 8.9 The owner away from home

- **Cloud:** the app works anywhere.
- **Home:** the owner's phone and laptop use the install's name everywhere. TLS ends at home, so the relay sees only the name, IP addresses, timing and volume. The care thread, inbox, timeline, `ExplainAnswer` and corrections come from the home core exactly as from the cloud ([03 §3.8.2](03-core-architecture.md#382-owner-corrections)).
- **Notifications:**
  - **Web Push from each edition's own server.** It's encrypted to the browser, so push services can't read it.
  - **Web push limits:**
    - iPhone and iPad get web push only in Home Screen web apps (iOS 16.4+).
    - Safari shows no action buttons.
    - A web app can't schedule local notifications.
    - "Persist until answered" is therefore repeated pushes collapsed by tag.
  - **The native owner shell.**
    - iOS: notifications with Taken / Snooze / Skip on the lock screen. Cloud sends through Apple's push service directly. Home sends through a content-blind push relay that forwards per-device ciphertext, which the app decrypts.
    - Android: a Trusted Web Activity that gets web push with actions.
  - **SMS, email (and WhatsApp and Discord in V2)** go through the cloud messaging bridge in both editions. While a home is offline, replies are sealed to the install's key, queued, and applied in order on reconnect.
  - **Sitters with several households.** Each active (sitter, household) pair gets its own Pawsitter sender number from a pool, and replies are routed by that number pair. When a reply's household is ambiguous, "TAKEN", "SKIP" or "SNOOZE" is never applied; the sitter gets one short link per household instead. "STOP" applies to that sender number only, and the delivery monitor tells owners when a sitter's SMS has been stopped.
- **iOS shell check before the home beta.** The iOS shell is a WKWebView app. WKWebView allows service workers only on up to 10 "App-Bound Domains", and in-app passkeys need the domain in the app's associated domains; neither is proven for an unbounded set of per-install names. If they don't work, the shell signs in to each install through the owner's Pawsitter account and keeps its offline data in native storage.

## 8.10 Outages and availability at home

In the cloud, a power cut at the house changes nothing. At home, a dark house would stop reminders and door codes for the very people standing in it. The fallbacks below are decided before the home beta (Q29), not left for later.

- **Backup reminders from the cloud.**
  - While a trip with medication routines is active, the home core keeps a rolling 48-hour schedule at the bridge: due instant, channel route, discreet text and task id. It never contains medication names.
  - The bridge sends a reminder only if the home hasn't marked it done or superseded by its due time. Replies are queued, sealed to the install.
  - On by default for medication trips; owners can opt out after a warning.
  - This is the one declared exception to the rule that companion services hold no care data.
- **Door codes staged on the sitter's phone.**
  - Each secret has a `needed_outside` flag. Readiness asks the owner to set it for every code a sitter needs to get in.
  - For flagged secrets, when the access window opens and after an online step-up, the home core seals the code to a non-extractable key on the sitter's device. It expires with access.
  - The reveal then works offline, is logged on the device, and syncs later. After the trip, the owner is prompted to rotate the code.
- **Readiness gate.** A medication trip at a home install isn't "ready" without backup reminders. It also isn't ready while any code a sitter needs at the door is neither staged nor covered by a stated fallback, such as a key left with a neighbor.
- **Power and wake.**
  - Setup recommends an always-on desktop or NAS.
  - The home core prevents idle sleep whenever any routine has reminders, not only during trips. A small helper ships for this: `caffeinate` on macOS, the service host on Windows.
  - Setup and readiness check sleep timers, lid and battery, automatic restart after power failure, FileVault, and the Windows power plan and wake timers.
  - The host is scheduled to wake ahead of each reminder.
  - Medication routines on a laptop host need an explicit "stays plugged in and open" confirmation.
- **Catch-up.** The reminder schedule is stored in SQLite. On every start or wake, reminders that came due in the gap fire at once, marked late.
- **Watchdog.**
  - Heartbeats are watched whenever any reminder is scheduled.
  - A missed heartbeat alerts the owner, and the sitter by SMS during a trip.
  - Each install's uptime is measured and shown in readiness, against the target of 99.5 % of reminders within a minute ([00 §0.8](00-product-offering.md#08-mvp-scope-and-success-measures)).
- **Clock trust.** The home core's clock is checked against the Home Link and NTP on every connect, and periodically after that. While it's unsynchronized, or earlier than the newest recorded time, dose answers are `unverified` and the reminders that depend on it are held. A Raspberry Pi has no real-time clock, so it needs one, or an NTP sync, before serving.
- **During an internet outage the sitter has:**
  - the offline copy, whose dose answers become `unverified`;
  - the printed care sheet with a dose log grid;
  - the cloud's backup reminders by SMS;
  - the staged door codes.

  Phones may leave a Wi-Fi network that has no internet for mobile data, which is one more reason the outage plan doesn't depend on the LAN.

## 8.11 Updates and data at home

**Code updates.**
- The runtime and the app bundle are updated through one signed manifest, applied automatically in stages.
- Security fixes ship within days. Other updates wait until no trip is active.
- Container installs use a thin launcher image that downloads, verifies and runs the signed runtime and bundle, or auto-update by default.
- The Home Link handshake enforces a minimum runtime. Owners are warned first; after a deadline, the relay stops routing known-vulnerable versions, but never in the middle of a trip without the owner's acknowledgement.
- Rollback restores the snapshot taken before each migration.
- Update keys live in an HSM with threshold signing, and every release is recorded in a public log.

**Data updates.**
- Signed time-zone snapshots, kill switches and minimum kernel versions ([07 §7.5](07-portable-core.md#75-time), [§7.8](07-portable-core.md#78-versions-replay-and-integrity)) are pushed down the Home Link within hours of approval. This channel is separate from code updates.
- Readiness flags any trip whose zones changed in a snapshot the install doesn't have yet.
- If a manifest expires while the home is offline, the home keeps the last valid snapshot and warns, instead of refusing.
- Re-expansion and the "a data update moved a dose time" alerts run at home. Only counts of affected schedules, with no content, go back for the release review.
- Every kernel build and snapshot the install has used is kept locally, so `ExplainAnswer` can replay.
- Text the home core builds (SMS, push, the console) uses only the kernel's local time fields, checked by lint.

## 8.12 Backups, keys and recovery at home

- **Local snapshots.** Daily, and before every migration, with a retention policy and free-space monitoring.
  - The live database folder is excluded from OS backups such as Time Machine and File History, which can copy it mid-write; the snapshot folder is included instead.
  - SD cards and USB sticks are refused as the data volume.
- **Encrypted off-site backup, free from the beta.** The structured data, which is small, and the wrapped key are encrypted on the device with a recovery key printed in the owner's recovery kit. Media backup is optional (Plus).
- **Restore onto new hardware.** After Pawsitter-account sign-in, a recovery code and alerts to every owner, the new machine re-binds the **same install id and name** with a new TLS key. Passkeys, Home Screen apps and printed cards keep working. A home core can also reclaim its own name by proving its long-term key.
- **Readiness shows** the age of the last backup and of the last test restore.
- **Key custody.** The key that unwraps the secret keys is protected by the platform where it can be: the System keychain on macOS, DPAPI or a TPM-backed key on Windows. On a NAS or Linux, the key is split: one share on disk, the other released by the hub over the Home Link only to the paired install. A stolen box that has been unpaired can't decrypt the door codes. The unwrapped key stays in memory while running, and a wrapped copy goes in the recovery kit.
- **Owners recovering away from home.** A couple travelling together can lose both phones in one bag. So:
  - **Remote recovery:** recovery codes can be kept in a password manager as well as on paper. A Pawsitter-account sign-in plus a recovery code, followed by a 24-hour delay with alerts to the other owners, admits a new device.
  - **A trip approver:** each trip can name one, such as a family member or the backup contact, who can approve joins and reset PINs.
  - **Sitters replace their own phone** with a code sent to the contact the owner entered.

## 8.13 Co-owners and account safety

- **Who controls the host.** Whoever administers the host can read its disk. Setup and owner settings say where the data lives and who controls it.
- **A tamper-evident log off the box.** Security events (sign-ins, console use, exports, unpairing, key access) are mirrored as metadata to a log every owner can see, together with the head of a hash chain over revisions, so tampering on the box is detectable.
- **Removing an owner.** Removing the last other owner takes effect only after a notice period, and the removed owner gets an export.
- **Every owner of a connected install has a Pawsitter account,** so every owner gets alerts and can lock remote access.
- **Account takeover.**
  - Locking remote access and unpairing need a passkey step-up and alert every owner.
  - A cloud-side unpair is a soft disable that can be undone for 7 days.
  - After any account recovery or contact change, that person's caregiver grants need the owner's re-approval.
  - Recovery codes never count toward the step-up for door codes.
  - Carrier SIM-swap checks are used where available.

## 8.14 What each companion service stores and sees

| Service | Stores | Can observe |
|---|---|---|
| Join routes | Which address each join id points to, with its expiry | When invites are created and claimed |
| Home Link hub | Install registry, link certificates, versions, heartbeats | When each home is online |
| Relay | Nothing | The install's name, IP addresses, timing and volume; never content |
| DNS and certificates | The zone's records | Certificate issuance (also public in CT logs) |
| Push relay | Device tokens bound to installs | Push timing; the payloads are ciphertext |
| Messaging bridge | Routes, number pools, a sealed queue with a time limit | SMS, email, WhatsApp and Discord content and numbers, as do the providers |
| Model proxy | Token counts and costs | Normal-tier prompts in transit, never stored |
| Watchdog and backup reminders | Heartbeats; a discreet 48-hour reminder schedule under opaque handles | When reminders are due, which hints at activity in the house |
| Update feed | Release metadata | Update checks |
| Off-site backup | Ciphertext | Size and timing |

The full inventory is published, and setup says plainly that SMS and email content passes through Pawsitter and its providers.

**If the companion services end**, or an owner stops paying, a documented exit applies: bring your own domain, DNS and tunnel, or run LAN-only with stated limits.

## 8.15 Moving between editions

Moving a household between cloud and home comes later (phase 4), but these rules are fixed now so it stays possible:
- **Identity.** User ids are UUIDv7 that Pawsitter ID can adopt unchanged, and revisions reference user ids, never passkey-specific handles.
- **Cutover:**
  - Moves happen only between trips.
  - Secrets are re-wrapped to the destination's key without plaintext leaving the source, after a 24-hour cooling-off that any owner can cancel.
  - The old address stays up for 30 to 90 days as a tombstone: it accepts and forwards queued facts and redirects everything else.
  - Each person gets a re-enrolment link, and printed cards keep working through the join domain.

## 8.16 Packaging and operations at home

- **Runtime.** Node 26 LTS in production for both editions: Active LTS since 2026-10-28, with end of life on 2029-04-30. The official Node binary ships inside each signed package with the app bundle. Single-file executables are deferred: Node's isn't finished and skips Intel Macs, and Bun's are large and need extra flags. Bun 1.4 stays compatible in CI. The kernel runs in worker threads with resource limits ([07 §7.9](07-portable-core.md#79-host-adapters)).
- **Platforms:**
  - **macOS:** a notarized `.pkg`. The server runs as a LaunchDaemon under a dedicated user, with data in `/Library/Application Support/Pawsitter`. Notarization needs the Apple Developer Program (US$99 a year).
  - **Windows:** a signed per-machine installer and a Windows service, with data in `ProgramData`. A firewall rule is added only when a LAN path is enabled, and setup detects a network marked Public.
  - **NAS, Linux, Raspberry Pi:** a multi-arch container image (amd64 and arm64) with a `/data` volume, a healthcheck, and compose and Unraid templates. An admin command, run with `docker exec`, handles recovery, invite QRs and claiming. The host's LAN address comes from configuration, because inside a container the server sees its own internal address.
  - **The tray app** (Tauri, at GA): status, join QRs, approvals, updates, power.
- **The port.** A fixed default that avoids common ones (3000, 5000/5001, 8080, 8123, 32400 and others), with a fallback to the next free port.
- **Support.** A consented diagnostics bundle goes over the Home Link: versions, heartbeats, certificate and backup state, error codes, and no household data. Owners and support also get a per-install health page.
- **Abuse.** Every install is a TLS endpoint with a valid certificate that Pawsitter can't inspect. So:
  - per-install bandwidth and connection quotas by plan;
  - detection of unusual traffic;
  - a takedown and appeal process;
  - the zone categorized with DNS-filter vendors before launch.
- **Uninstalling.** Export, destroy the keys, unpair, clean up DNS, and notify members and sitters.

## 8.17 Phasing

| Phase | Scope |
|---|---|
| **0. Foundations** (now) | **Build:** the monorepo, kernel, core and ports; both stores behind one contract; the test kit running both compositions; sign-in (devices, grants, joins, passkeys, codes, step-up).<br>**Long-lead items:** settle the name (Q20); register the home zone; apply for the Public Suffix List; request the Let's Encrypt rate-limit exemption; set up a backup CA.<br>**Fix now:** the identity rules for moving between editions (§8.15). |
| **1. Cloud MVP** | The spec's MVP, plus:<br>- sitters as global users with per-account device grants;<br>- sent, displayed and printed QR joins with a second factor bound to the browser;<br>- linked devices and the security log;<br>- passkeys, the offline copy and web push;<br>- two-way SMS with number pools;<br>- the iOS shell and Android TWA, if they're in the MVP (Q32). |
| **2. Home beta** (internet required) | **Hosts:** the container image and an always-on Mac only, with one sign-in preset.<br>**Services:** the Home Link, relay, DNS and certificates; the push relay, bridge, model proxy and watchdog.<br>**Outage and recovery:** backup reminders and staged door codes; encrypted off-site backup and restore.<br>**Updates:** signed code and data updates.<br>**Testing:** the same end-to-end suite, and passkey tests on real devices with real certificates.<br>**Zone:** a separate, invite-only one. |
| **3. Home GA** | Windows; the tray app; the desktop LAN shortcut; the kiosk; Pawsitter-account sign-in for homes; local models and the owner's own model key; CT monitoring for owners; the production zone once the Public Suffix List entry has shipped. |
| **4. Later** | Moving households between editions; WhatsApp and Discord (V2); a split-DNS guide; a single-file runtime. |

## 8.18 Open decisions and hypotheses

**For the owner to decide** (in [05](05-open-questions.md)):
- **Q27:** home relay-first.
- **Q28:** the home sign-in defaults, the menu in §8.6.
- **Q29:** outage fallbacks.
- **Q30:** the home-zone domain.
- **Q31:** home pricing.
- **Q32:** whether the iOS shell is in the cloud MVP.

**Adopted as defaults, open to revisit:**
- a LaunchDaemon on macOS;
- the Node 26 binary plus a bundle, not a single-file executable;
- one account per install;
- no no-login options in the beta;
- a Pawsitter account required for every owner of a connected install.

**Hypotheses to test on real devices before the phase that depends on them:**
- the Web Push rules on iOS;
- Safari's 7-day storage eviction for sites not on the Home Screen;
- how cookies carry over to a Home Screen app;
- App-Bound Domains and associated domains for per-install names (§8.9);
- Windows firewall prompts and Microsoft's signing service;
- FileVault after a power cut;
- Trusted Web Activity asset links per install;
- Apple's critical-alert entitlement;
- how common router rebinding filters are, and guest-network isolation by router brand;
- WhatsApp webhook rules;
- whether phones leave a Wi-Fi network that has no internet;
- Chrome possibly gating top-level navigations to local addresses.

Until each is confirmed, its worst-case fallback applies. For example, assume a per-install TWA can't verify its asset links, and send its push through the relay.
