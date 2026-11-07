# 8. Home and cloud editions

One codebase runs in two ways: as a hosted service (**cloud**), or on the owner's own always-on computer or NAS (**home**). A home install is either *connected* to Pawsitter's companion services or runs *standalone*, with only what the owner sets up (§8.15). In every case, a sitter gets set up by scanning a QR code.

How this was decided, on 2026-11-04:
- Four research areas (HTTPS on a home network, sign-in and pairing, remote access and push, packaging) were fact-checked: 142 checks, with 77 confirmed, 22 corrected and 43 unverifiable. Most unverifiable ones match known facts but weren't re-read; those that need testing on real devices are listed as hypotheses in §8.19.
- Three independent designs were then written (simplicity first, unified experience first, security first). A judge scored them, picked "unified experience" (22 points, against 21 and 20) and grafted in 23 ideas from the other two.
- A red-team review followed, and its fixes are built in below.

## 8.1 The decisions

1. **One TypeScript codebase, two composition roots.** *Cloud* is multi-tenant: Postgres, S3, KMS. *Home* serves one household from an always-on Mac, Windows PC or NAS: SQLite, local disk, a local key. Each account's data lives in exactly one of them (README principle 8).
2. **Connected home installs are relay-first.** Each one gets its own HTTPS name. Pawsitter's relay passes encrypted traffic through to it without decrypting, so the same address works on the home Wi-Fi, guest Wi-Fi, mobile data and abroad, with no port forwarding (§8.4).
3. **One QR join for both editions.** A code that's sent, shown on a screen or printed opens the same join flow. A second factor binds it to the right person (§8.7).
4. **Every sitter is a real, lightweight user.** No password, no app and no sign-up form, but their own identity, with access bounded by the trip and revocable at once.
   - Cloud sitters have one login across every household they sit for.
   - Home sitters are local to the install, and can link a Pawsitter account (§8.5).
   - This replaces the no-account sitter link (Q11).
5. **Home owners choose their sign-in options from a menu** with a recommended default (§8.6).
6. **Companion services hold operational records such as routing data and ciphertext, never care records** (§8.14). These are the relay, DNS and certificates, push relay, messaging bridge, model proxy, watchdog and updates. The one declared exception is a discreet reminder schedule that keeps medication reminders going if the home goes dark (§8.10).
7. **A home install can also run standalone**, without Pawsitter's services. It uses what the owner sets up, such as Tailscale, their own domain, a Discord bot and their own backup target, and does as much as those allow (§8.15).

**Why not just serve plain HTTP on the home network?**
- An address like `http://192.168.1.20` isn't a secure context. Browsers then give no passkeys, no service worker (so no offline copy and no web push), no camera, no `crypto.subtle` and no `Secure` cookies. All of this was checked in Chrome 153.
- Self-signed certificates don't help: browsers refuse passkeys and service workers on pages with certificate errors, and asking every sitter to trust a private certificate authority on their iPhone isn't realistic.
- Guest Wi-Fi often isolates guests from the home network.
- A server that only works inside the home can't reach the owner while they're away on the trip.

## 8.2 What each edition promises

| Situation | Cloud | Home, connected | Home, standalone (§8.15) |
|---|---|---|---|
| Where household data lives | Pawsitter's cloud | The owner's computer or NAS | The owner's computer or NAS |
| Owner away on the trip | Works anywhere | Works anywhere, through the relay | Through Tailscale or the owner's own domain, if set up |
| Sitter on mobile data or guest Wi-Fi | Works | Works, through the relay | Through Tailscale Funnel or the owner's own domain; otherwise Discord and the printed care sheet |
| Home internet down | Unaffected | Offline copy, printed care sheet, cloud backup reminders and door codes staged on the sitter's phone; reminders and the copy's tasks cover about 48 hours (§8.10) | Offline copy, printed care sheet, staged door codes and dose alarms on the sitter's phone; no reminders from outside |
| Pawsitter's cloud down | Down | The home keeps running and sends web push, but its name routes through the relay: without split DNS, even people in the house have only the offline copy. SMS, email and native push stop | Unaffected |
| Host computer asleep or off | n/a | Like an internet outage; the watchdog alerts the owner | Like an internet outage; the owner hears only through an outside monitor they set up |
| Owner needs a Pawsitter account | Yes | Yes (pairing, relay, alerts, billing); the data stays home | No |
| Owner's effort | None | An always-on machine; certificates, updates and backups are automatic | Also setting up the ways in, notifications and a backup target; after that, certificates and backups are automatic |

Both home modes keep data **at rest** at home. A connected install still relies on Pawsitter for the relay, DNS, certificates, SMS, email and native push; a standalone one relies only on the services its owner set up. Setup says so plainly, with this table.

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
- the notifiers that send through the companion services or, standalone, through the owner's own accounts;
- the tray app and the installers.

**Nothing in the kernel or services knows which edition it's in.** An edition is only a choice of adapters at the composition root, plus `CallerContext.transport` (`loopback`, `lan`, `relay`, `tunnel` or `cloud`). One contract and end-to-end suite runs against both compositions.

**Home topology.** The home core runs under a dedicated OS user and holds the kernel, services, SQLite database, media, keys, jobs and the web app.
- Listeners:
  - `localhost`, for the setup and recovery console only;
  - no inbound ports from the internet;
  - an optional LAN listener (§8.4) that checks every `Host` header against the install's names.
- On a connected install, one outbound **Home Link**, mutual TLS with a certificate from Pawsitter's private CA, issued at pairing. It carries:
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
  - The zone is to be listed in the Public Suffix List, applied for on isolation grounds, so installs are isolated from one another as separate sites. Without that listing, one install could set cookies on every other. The PSL has no service-level agreement and declines some new projects, so the listing isn't guaranteed.
  - Until the listing ships in current Chrome, Safari and Firefox, the beta runs on a separate, invite-only zone.
- **Certificates.** The home core generates its own key and sends only a certificate request; the private key never leaves home. One certificate covers the name and its subdomains, validated through a DNS API scoped to that install.
  - CAs: Let's Encrypt is primary. A backup CA is reached through a Pawsitter-run ACME proxy, so no shared CA account key is ever stored on installs.
  - Renewal: through ACME Renewal Information, and again at startup, because a machine may be off for weeks.
  - Lifetimes are shrinking. The CA/Browser Forum maximum is 200 days now and 100 days from March 2027. Let's Encrypt's default certificates last 90 days now, 64 days from February 2027 and 45 days from February 2028.
  - Rate limits: until Let's Encrypt grants a rate-limit override (the request takes a few weeks) or the Public Suffix List entry arrives, Let's Encrypt issues only 50 new certificates per registered domain per week. Installs keep their key and certificate across reinstalls.
  - DNS: CAA records name both CAs.
  - Transport: home cores never advertise HTTP/3, because the relay carries TCP only.
- **Trust, stated plainly.** Pawsitter controls the zone's DNS and so could obtain a certificate for any install. Keys never leave home, and owners can audit issuance in the public CT logs.
- **LAN paths** (all optional):
  - *Desktop LAN shortcut* (home GA): a stable `lan` name under the install, under a random label, that points at the machine's LAN address and is updated when DHCP changes. Some routers and DNS filters drop answers that point at private addresses; the tray app detects that and falls back to the relay.
  - *Split DNS* (power users): point the install's name at the LAN address in the router.
  - *Console* on the host itself (`http://localhost`): setup and recovery only.
- **No plain-HTTP mode for sitters.** "Basic LAN mode" was considered and dropped. It conflicts with the rule that medical data needs HTTPS ([07 §7.12](07-portable-core.md#712-open-items)), and its cookies leak to every other service on the same host. It also doesn't help in an outage, because the sitter needs it set up in advance on a second address. The outage plan is §8.10.
- **Standalone installs** don't use the home zone. They're reached through Tailscale, Tailscale Funnel or the owner's own domain (§8.15).
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
  - On a connected install, a person can link a Pawsitter account through OIDC; the home core stays the authority for membership and revocation.
  - A Pawsitter account that's disabled is pushed down the Home Link and applied on receipt.
  - One install hosts one account.
- **Caller context.** `CallerContext` gains:
  - `transport`: `loopback`, `lan`, `relay`, `tunnel` or `cloud`;
  - `device_id`;
  - `auth_strength`: `passkey_uv`, `otp_verified`, `approved`, `pin` or `session`.

  All three come from the connection and the credential, never from the request. Transport is recorded for audit and never raises trust, and relayed traffic is never treated as local.
- **Step-up for door codes and medication-order changes.** Either of these, both scoped per device and account:
  - a passkey with user verification within 5 minutes;
  - a code verified within 24 hours ([04 §4.2](04-permissions-privacy.md#42-time-boxed-access)).

  Inside the home with no internet, a personal PIN or live owner approval works instead, but only where split DNS keeps the install's name reachable; otherwise door codes come from those staged on the sitter's phone (§8.10). Secrets are never served over plain HTTP, and recovery codes never count as a step-up.

## 8.6 Home sign-in options

Sign-in is always on, but nobody types a password. People join once by QR, and the owner chooses how strict each step is.

| Option | How it works | Revoking | Works with no internet | Default |
|---|---|---|---|---|
| **Paired devices** | Each phone or computer joins once by QR and keeps a device session (an `HttpOnly` cookie on the install's name). Caregiver sessions end with the trip. | Revoke the device or remove the person; the next request is refused | Only with split DNS (the name needs DNS) | **Sitters and family** |
| **Passkeys** on the install's name | Checked by the home core itself. Synced by iCloud Keychain and Google Password Manager; works across the relay name and the LAN shortcut. | Delete the passkey and its sessions | Only with split DNS | **Owners and admins**, with a printed recovery kit; offered to everyone |
| **One-time code** to a contact the owner entered | 6 digits, 10 minutes, 5 tries, sent by SMS or email through the bridge, only to a number or address the owner typed | Codes expire; changing the contact cancels pending ones | No | **The join check for sitters** with a contact on file; the online step-up for door codes |
| **Owner approval** | The joining device shows match words; an owner approves inside the Pawsitter app, seeing the person, device, time, approximate location and network | Deny, or revoke later | Only with split DNS | **Card joins**, sitters with no contact on file, and new owner devices if the owners require it |
| **Personal PIN** | 6 to 8 digits, set by a paired person, bound to that device; re-unlocks the app and serves as the offline step-up | An owner or the trip's approver resets it | Only with split DNS | **On** as the offline step-up |
| **Pawsitter account** (OIDC) | Sign in with an existing Pawsitter account; the owner still approves the first device | Remove the person locally; a cloud-side disable arrives as an event | No | **Owners**, from the beta, for remote recovery (§8.12). Off for family and sitters; offered at GA to those who use Pawsitter elsewhere |
| **Console** (`http://localhost`) | On the host only, behind the OS login plus a console token | Rotate the token | Yes | **Always on**, for setup and recovery |
| **Kiosk device** | A paired tablet shows Today, what's next and the emergency card. It can tick non-medication tasks, and can never record a dose, reveal a code or show private data. | Revoke the kiosk | Only with split DNS | Off |
| Trusted home Wi-Fi (no sign-in) | Anyone on the home network sees a read-only Today view | Change the Wi-Fi password | Only with split DNS | **Not recommended; not offered in the beta.** The LAN is not a trust boundary, and the kiosk covers the need. |
| Shared household PIN | One PIN unlocks a person picker | Change the PIN for everyone | Only with split DNS | **Not recommended; not offered in the beta.** No per-person attribution or revocation. |

**Recommended default**, preselected at setup:
- **Owners and admins:** a passkey, a printed recovery kit (also saved to a password manager), and a second owner where possible. New owner devices need a passkey, confirmation on one of that owner's signed-in devices, or a recovery code, and every owner is alerted; owners can also require a second owner's approval.
- **Family:** a QR join approved by an owner.
- **Sitters:**
  - A QR join that becomes a paired device ending with the trip.
  - The join check is a code to the contact the owner entered. With no contact on file, or a printed-card join, the owner approves instead. At a displayed QR, the owner approves on the spot.
  - A passkey is offered, never required.

**The beta ships one preset:** passkeys for owners, paired devices for family and sitters (joined with a code or owner approval), and a PIN for the offline step-up. The kiosk, and Pawsitter-account sign-in for family and sitters, arrive at GA. Owners can sign in to the install with their Pawsitter account from the beta, for remote recovery and, if the per-install test fails, the iOS shell (§8.9). The two no-login options aren't offered.

**Standalone installs** offer the same menu without Pawsitter-account sign-in. Codes go through the owner's own email account, SMS provider or Discord bot (§8.15).

## 8.7 Joining by QR

**Rules for every join, in both editions:**
- **The link.** Every QR opens a link on Pawsitter's join domain, which redirects (a top-level navigation, never a background request) to the account's own address: the cloud, or the home install. A standalone install's QR codes point straight at its own address.
- **The secret.** It's only in the URL fragment (`#…`), so it never reaches server logs, `Referer` headers or link previews. Opening the page consumes nothing. Tapping Continue sends the secret by POST and starts a join request; the secret is spent only when the second factor passes.
- **What the page reveals.** Until the second factor passes, only "Invite for <name> from <owner's first name>": no dates and no address, which would reveal an empty house.
- **The second factor is tied to this browser.** It's a code sent to the contact the owner entered, or the owner's approval. The confirming link works only in the browser that started the request. Anywhere else, it says "this request started on another device". A typed code is the fallback.
- **The SMS wording:** "Pawsitter code to add a device for <household>. Only enter it at <domain>."
- **In-app browsers.** Gmail and similar apps open links in their own browser, with its own cookies. After joining there, the page offers a one-time link to continue in the phone's real browser. On iPhone it also offers Add to Home Screen, which web push needs, and continues the session inside the installed app.
- **The owner sees every join:** "Claimed by Jamie's iPhone, Safari, 18:02", with Revoke. Reusing a spent link alerts the owner and names the device.
- **Approval requests** go to every owner and admin and to the trip's approver on all their channels, including SMS as a link that opens the app. Approving still happens only inside the app.

| | Sent invite | Displayed join window | Printed home card |
|---|---|---|---|
| **What it is** | A link (and its QR, shown on the owner's own screen) sent by message, SMS or email | A QR plus a short code, shown on the owner's phone, the tray app or a kiosk | A card on the fridge or the care sheet: a QR, the plain domain and a short household code to type |
| **Secret** | 256 random bits, spent once its device limit is reached; the owner can resend, which rotates it | 128-bit nonce, rotating every 30 seconds (each lives at most 60 seconds), plus a 6-character code valid 2 minutes | None. The card holds a random locator that grants nothing on its own and can be rotated or disabled. |
| **Valid** | Until the trip's access ends, or 14 days after sending for an invite with no trip; a sitter can join early, and their session doesn't idle out before the trip | While the window is open (10 minutes by default; the owner can lengthen it) | Only while a trip's access window is open (from 24 hours before) or the owner has opened a join window |
| **Second factor** | A code to the contact the owner entered, or owner approval | The owner approves on the spot; at an unattended kiosk, the trip's join check | Owner approval with match words (the default); or, if the owner allows it, the person's name plus the contact the owner registered, then a code |
| **Devices** | Two by default (a phone and a tablet), with owner alerts | First join closes the window | One per request |
| **Limits** | 5 failed claims lock the invite and alert the owner | 5 code attempts per window | 5 requests an hour and 20 a day per card; owner alerted on every request; identical responses, so nobody can probe which contacts exist |

**Recovering a spent or lost invite.** The verified contact can re-claim on a new device with a fresh code; this replaces the old device. Locked invites can be reset by the owner or the trip's named approver (§8.12).

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
  - revoke an invite, or rotate a printed card;
  - sign out everywhere;
  - at home, lock remote access.
- **What revoking does.** Everything happens in one transaction, with revisions and events:
  - live streams close;
  - push subscriptions and native push bindings are removed;
  - deleted passkeys are hidden in Chrome and Safari password managers through the WebAuthn Signal API.
- **Ended is not revoked.** A trip ending must never lose a dose.
  - The phone's outbox of unsent doses and task completions is never wiped by a refused request; only the read cache is.
  - An *ended* caregiver device keeps a limited grant for 7 days. It can still send administrations, completions and reveal logs whose device time falls inside the access window. They're flagged late-synced, and the owner is alerted at once.
  - A *revoked* device gets one quarantined upload, which the owner reviews.
  - Before closing, "I'm home" warns: "Jamie's phone last synced 19:40 and may have unsent entries". The sitter sees "N entries not sent", with an SMS fallback.
  - For those 7 days, an ended device can still read the sitter's own events and the stay summary, which is also sent to the sitter ([04 §4.2](04-permissions-privacy.md#42-time-boxed-access)).
- **The offline copy after revoking.**
  - It's encrypted under a key the server leases to the device for 24 to 48 hours and renews while online, so a revoked device loses access when the lease lapses. While a home install is unreachable, the hub hands out renewals the home core deposited ahead, but never to a revoked device (§8.10).
  - It refuses to open if the device clock is earlier than the last server time it saw.
  - It holds tasks only 48 hours ahead, not the whole stay.
  - The revoke dialog says plainly that revoking can't erase what's already on the phone, and suggests rotating every code that was revealed on it or staged to it.
- **At home:**
  - Revoking works locally even when Pawsitter's cloud is down.
  - On a connected install, an owner can also use their Pawsitter account to send a signed "revoke this device" command down the Home Link. If the house is unreachable, they can instead lock remote access, which tells the relay to stop routing the install. Both need a passkey step-up and alert every owner.
  - A standalone install can be reached for revoking only through its own ways in. While it's unreachable, a revoked device keeps what it has until its lease lapses.

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
  - **SMS, email (and WhatsApp and Discord in V2)** go through the cloud messaging bridge in the cloud and on connected installs. While a home is offline, replies are sealed to the install's key, queued, and applied in order on reconnect.
  - **Standalone installs** send web push, Discord messages from the owner's bot, email through the owner's account, and SMS only through the owner's own provider (§8.15).
  - **Sitters with several households.** Each active (sitter, household) pair gets its own Pawsitter sender number from a pool, and replies are routed by that number pair. When a reply's household is ambiguous, "TAKEN", "SKIP" or "SNOOZE" is never applied; the sitter gets one short link per household instead. "STOP" applies to that sender number only, and the delivery monitor tells owners when a sitter's SMS has been stopped.
- **iOS shell check before the home beta.** The iOS shell is a WKWebView app. WKWebView allows service workers only on up to 10 "App-Bound Domains", and in-app passkeys need the domain in the app's associated domains; neither is proven for an unbounded set of per-install names. If they don't work, the shell signs in to each install through the owner's Pawsitter account and keeps its offline data in native storage.

## 8.10 Outages and availability at home

In the cloud, a power cut at the house changes nothing. At home, a dark house would stop reminders and door codes for the very people standing in it. The fallbacks below are decided before the home beta (Q29), not left for later. Standalone installs can't use the parts that need the cloud; their plan is in §8.15.

- **Backup reminders from the cloud.**
  - While a trip with medication routines is active, the home core keeps a rolling 48-hour schedule at the bridge: due instant, channel route, escalation routes, repeat policy, discreet text and task id. It never contains medication names.
  - The home core sends these reminders itself and holds a short claim on each entry. Once someone answers, it closes the entry at the bridge, and it keeps renewing the claim until the bridge confirms the close. If a claim lapses first, the bridge takes over that entry and follows the routine's reminder policy: it repeats the reminder until someone replies "TAKEN" or "SKIP" ("SNOOZE" only delays the next repeat), and escalates to the owner and the backup contact if nobody does. Replies are queued, sealed to the install.
  - On by default for medication trips; owners can opt out after a warning.
  - This is the one declared exception to the rule that companion services hold no care data.
- **Door codes staged on the sitter's phone.**
  - Each secret has a `needed_outside` flag. Readiness asks the owner to set it for every code a sitter needs to get in.
  - For flagged secrets this sitter may reveal (the trip grants `secrets.reveal` and the secret's policy allows it), when the access window opens and after an online step-up, the home core seals the code to a non-extractable key on the sitter's device. It expires with access. A code rotated during the window must be staged again; until it is, readiness flags the stale copy.
  - That step-up covers later reveals of the staged copy, which work offline, are logged on the device and sync later. After the trip, the owner is prompted to rotate the code.
- **Readiness gate.** At a home install, no trip is "ready" while a code a sitter needs at the door has no stated fallback, such as a key left with a neighbor, and can't be staged: the sitter must be allowed to reveal it and their device must have joined. Once access opens, readiness checks it's staged. A medication trip also isn't ready without backup reminders.
- **Power and wake.**
  - Setup recommends an always-on desktop or NAS.
  - The home core prevents idle sleep whenever any routine has reminders, not only during trips. A small helper ships for this: `caffeinate` on macOS, the service host on Windows.
  - Setup and readiness check sleep timers, lid and battery, automatic restart after power failure, FileVault, and the Windows power plan and wake timers.
  - The host is scheduled to wake ahead of each reminder.
  - Medication routines on a laptop host need an explicit "stays plugged in and open" confirmation.
- **Catch-up.** The reminder schedule is stored in SQLite. On every start, wake or Home Link reconnect, the home first applies the replies queued at the bridge, then takes back the reminders still open: those the bridge never sent fire at once, marked late; the rest continue their repeats and escalation.
- **Watchdog.**
  - Heartbeats are watched whenever any reminder is scheduled.
  - A missed heartbeat alerts the owner. During a trip it also alerts the sitter by SMS, and the backup contact if no owner acknowledges it within 30 minutes.
  - Each install's uptime is measured and shown in readiness, against the target of 99.5 % of reminders within a minute ([00 §0.8](00-product-offering.md#08-mvp-scope-and-success-measures)).
- **Clock trust.** The home core's clock is checked against the Home Link and NTP on every connect, and periodically after that. While it's unsynchronized, or earlier than the newest recorded time, dose answers are `unverified` and the reminders that depend on it are held. A Raspberry Pi 4 has no real-time clock, so a Pi-class host needs a battery-backed clock, or an NTP sync, before serving.
- **During an internet outage the sitter has:**
  - the offline copy, whose dose answers become `unverified`;
  - the printed care sheet with a dose log grid;
  - the cloud's backup reminders by SMS;
  - the staged door codes.

  Phones may leave a Wi-Fi network that has no internet for mobile data, which is one more reason the outage plan doesn't depend on the LAN.
- **How long this lasts.** Backup reminders and the offline copy's tasks reach 48 hours past the home's last contact, and the watchdog's alerts say so. After that, the sitter has the printed care sheet and the staged door codes. So that the care guide and emergency card stay readable through an outage, the home core deposits each device's lease renewals with the hub, sealed to that device. Revoking a device or ending its trip withdraws its deposits. While the home is unreachable, the hub releases them, except to a device an owner has revoked from their Pawsitter account.

## 8.11 Updates and data at home

**Code updates.**
- The runtime and the app bundle are updated through one signed manifest, applied automatically in stages.
- Security fixes ship within days. Other updates wait until no trip is active.
- Container installs use a thin launcher image that downloads, verifies and runs the signed runtime and bundle, or auto-update by default.
- The Home Link handshake enforces a minimum runtime. Owners are warned first; after a deadline, the relay stops routing known-vulnerable versions, but never in the middle of a trip without the owner's acknowledgement.
- Migrations are additive: a release only adds, and a later release removes what's no longer used, so the previous release still runs on the new schema and rolling back means reinstalling it. The pre-migration snapshot is restored only if the new version never accepted a write; otherwise the fix rolls forward. A rollback never discards a recorded fact ([02 invariant 20](02-domain-model.md#218-invariants-enforced-by-the-core)).
- Update keys live in an HSM with threshold signing, and every release is recorded in a public log.
- Standalone installs check the public release feed, sending only their version, or are updated by hand (§8.15).

**Data updates.**
- Signed time-zone snapshots, kill switches and minimum kernel versions ([07 §7.5](07-portable-core.md#75-time), [§7.8](07-portable-core.md#78-versions-replay-and-integrity)) are pushed down the Home Link within hours of approval. This channel is separate from code updates.
- Readiness flags any trip whose zones changed in a snapshot the install doesn't have yet.
- If a manifest expires while the home is offline, the home keeps the last valid snapshot and warns, instead of refusing.
- Re-expansion and the "a data update moved a dose time" alerts run at home. Only counts of affected schedules, with no content, go back, and they gate the later stages of the rollout ([07 §7.5](07-portable-core.md#75-time)).
- Every kernel build and snapshot the install has used is kept locally, so `ExplainAnswer` can replay.
- Text the home core builds (SMS, push, the console) uses only the kernel's local time fields, checked by lint.

## 8.12 Backups, keys and recovery at home

- **Local snapshots.** Daily, and before every migration, with a retention policy and free-space monitoring.
  - The live database folder is excluded from OS backups such as Time Machine and File History, which can copy it mid-write; the snapshot folder is included instead.
  - SD cards and USB sticks are refused as the data volume.
- **Encrypted off-site backup, free from the beta.** The structured data, which is small, and the wrapped key are encrypted on the device with a recovery key printed in the owner's recovery kit. Media backup is optional (Plus). Standalone installs back up to a target the owner sets up (§8.15).
- **Restore onto new hardware.** After Pawsitter-account sign-in, a recovery code and alerts to every owner, the new machine re-binds the **same install id and name** with a new TLS key. Passkeys, Home Screen apps and printed cards keep working. A home core can also reclaim its own name by proving its long-term key. A standalone install restores from its own backup with the recovery kit, and keeps its address if the owner moves that name to the new machine.
- **Readiness shows** the age of the last backup and of the last test restore.
- **Key custody.** The key that unwraps the secret keys is protected by the platform where it can be: the System keychain on macOS, DPAPI or a TPM-backed key on Windows. On a NAS or Linux, the key is split: one share on disk, the other released by the hub over the Home Link only to the paired install (standalone: a passphrase or a key file, §8.15). A stolen box that has been unpaired can't decrypt the door codes. The unwrapped key stays in memory while running, and a wrapped copy goes in the recovery kit. So a NAS or Linux install that restarts without internet can't reveal secrets until the Home Link returns; staged door codes (§8.10) cover that gap.
- **Owners recovering away from home.** A couple traveling together can lose both phones in one bag. So:
  - **Remote recovery:** recovery codes can be kept in a password manager as well as on paper. A Pawsitter-account sign-in plus a recovery code, followed by a 24-hour delay with alerts to the other owners, admits a new device.
  - **A trip approver:** each trip can name one, such as a family member or the backup contact, who can approve the trip's joins, reset PINs and reset locked invites.
  - **Sitters replace their own phone** with a code sent to the contact the owner entered.

## 8.13 Co-owners and account safety

- **Who controls the host.** Whoever administers the host can read its disk. Setup and owner settings say where the data lives and who controls it.
- **A tamper-evident log off the box.** Security events (sign-ins, console use, exports, unpairing, key access) are mirrored as metadata to a log every owner can see, together with the head of a hash chain over revisions, so tampering on the box is detectable. Standalone installs send them to a private Discord channel or the owner's email instead (§8.15).
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
| Home Link hub | Install registry, link certificates, versions, heartbeats; for NAS and Linux installs, one share of the key that unwraps door codes (§8.12); sealed lease renewals for offline copies (§8.10) | When each home is online |
| Relay | Nothing | The install's name, IP addresses, timing and volume; never content |
| DNS and certificates | The zone's records | Certificate issuance (also public in CT logs) |
| Push relay | Device tokens bound to installs | Push timing; the payloads are ciphertext |
| Messaging bridge | Routes, number pools, a sealed queue with a time limit, and SMS counts and costs | SMS, email, WhatsApp and Discord content and numbers, as do the providers |
| Model proxy | Token counts and costs | Normal-tier prompts in transit, never stored |
| Watchdog and backup reminders | Heartbeats; during a trip, opaque contact handles for the sitter and the backup contact, and a discreet 48-hour reminder schedule under opaque handles | When a trip is on and when reminders are due, so when the house may be empty |
| Update feed | Release metadata | Update checks |
| Off-site backup | Ciphertext | Size and timing |
| Security log mirror | Security events as metadata (sign-ins, console use, exports, unpairing, key access) and the head of the revision hash chain (§8.13) | Who signs in, exports or unpairs, and when |
| Pawsitter ID | Owners' accounts and billing, and which people linked a Pawsitter account to which install (§8.5) | Sign-ins, and which installs each linked person uses |

The full inventory is published, and setup says plainly that SMS and email content passes through Pawsitter and its providers.

**If the companion services end**, every install can switch to standalone mode (§8.15). Stopping Plus never removes the free companion services ([00 §0.7](00-product-offering.md#07-packaging-proposal)).

## 8.15 Standalone mode

Decided (2026-11-07): a home install can also run **without Pawsitter's services**. It then uses only what the owner sets up: their own network, and accounts they hold with services such as Tailscale or Discord. Pawsitter holds nothing about the household, not even an owner's account. The install's only contact with Pawsitter is an anonymous check for updates, which the owner can turn off.

Everything that doesn't need a companion service works as on a connected install: the kernel and dose safety, the care thread, joins and sign-in, staged door codes and the offline copy. For each companion service, the install uses what the owner set up in its place, or goes without, and setup and readiness say which. Setup asks whether to connect the install or run it standalone; switching later is in §8.16.

| Companion service | Standalone, it uses | What's missing |
|---|---|---|
| Relay, DNS and certificates | At least one way in that the owner sets up (below) | With none, phones can't open the install: only the console on the host and the Discord bot work |
| Join routes | QR codes and links that point straight at the install's own address | Passkeys and printed cards stop working if that address changes |
| Push relay | Web push, sent straight from home, and notifications from the owner's Discord bot | Taken / Snooze / Skip on the iOS lock screen. On iPhone, web push needs the Home Screen web app |
| Messaging bridge | The owner's Discord bot (below); email through the owner's own account; SMS only through the owner's own provider, which in the US needs carrier registration (A2P 10DLC or toll-free verification) | Texts to sitters who don't use Discord, unless the owner brings an SMS provider |
| Model proxy | A local model, or the owner's own AI provider key | The hosted assistant (Plus) |
| Watchdog and backup reminders | Heartbeats to a monitor the owner chooses, such as a Healthchecks.io check or Uptime Kuma on a machine outside the house, which alerts them its own way | Reminders from outside while the house is dark (below) |
| Update feed | The public release feed, checked anonymously, or updates by hand. Releases are signed either way | Prompt security fixes and time-zone data, if the feed is off. Readiness shows how old the software and time-zone data are |
| Off-site backup | Encrypted backups to a target the owner sets up: another disk, a NAS share, an S3-compatible bucket, or a machine on their tailnet | Nothing, once a target is set |
| Security log mirror | Security events sent to a private Discord channel or the owner's email, as the copy off the box | Tamper evidence, if neither is set |
| Pawsitter ID | Accounts local to the install | Remote recovery through a Pawsitter account; owners recover with the printed kit |
| Home Link hub | On a NAS or Linux host, a passphrase typed at the console after a restart, or a key file on a USB stick, as the second key share. If the owner chooses, offline-copy leases as long as the trip, since nothing outside can renew them | Door-code reveals after an unattended restart until the owner unlocks, though staged codes still work. A longer lease keeps a revoked device's copy readable longer |

**Ways in.** HTTPS is still required (§8.4). The owner sets up at least one:
- **Tailscale, for the household's own devices.** Owners and family run Tailscale. The install gets a `<machine>.<tailnet>.ts.net` name with a Let's Encrypt certificate, so passkeys, the offline copy and web push all work. A sitter would have to install Tailscale too.
- **Tailscale Funnel, for sitters.** It publishes the install's HTTPS name on the internet, so sitters need nothing installed. Tailscale's relays pass the traffic through without decrypting it, and TLS still ends on the home machine. Funnel is on every Tailscale plan.
- **The owner's own domain.** The install gets certificates through the owner's DNS provider, so the key stays at home. It's reached on the home network through a local DNS record, by port forwarding, or through a tunnel. A tunnel such as Cloudflare's decrypts traffic at its edge, so Cloudflare can see what passes through.
- Whichever way is used, the install's name is published in Certificate Transparency logs, so setup suggests one that doesn't identify the household. Requests through Tailscale, Funnel or a tunnel are recorded as transport `tunnel` and, like relayed ones, never raise trust.
- **A house with no internet at all** could use a private certificate authority that the owner installs by hand on each household device (later). Sitters can't reasonably do that, so they use the printed care sheet.

**Discord as the messaging channel.**
- The owner creates a bot in Discord's developer portal and enters its token in setup. The token stays on the install.
- The bot connects out to Discord and receives button presses over that same connection, so it needs no open port, tunnel or public address.
- Discord can read these messages, so discreet mode is on by default: a reminder says "Sonic's 8 pm dose, item 2 on the care sheet" rather than naming the medication, unless the owner allows names.
- With Discord and no way in, a sitter still gets reminders, answers them and can ask questions in the care thread; the printed care sheet covers the rest.

**The owner's side of a trip.** Wherever an owner follows trips on Discord, they get:
- the assistant's answers to the sitter: those about medication, health and incidents at once, or every one if the owner chooses (Q22);
- questions the assistant couldn't answer from the records ([03 §3.8](03-core-architecture.md#38-how-the-ai-assistant-plugs-in));
- dose alerts, incidents, photo updates and the daily report.

They reply to an answer to correct it, or to a question to answer it. The reply reaches the sitter on whatever channel they use, and a change to the records comes back as a draft with an Apply button ([03 §3.8.2](03-core-architecture.md#382-owner-corrections)). Join approvals still open in the app.

There are two ways to set it up:
- **On a server.** The owner adds the bot to a server: one made for the household, or one they already have for other things. The bot creates the channels and sets who can see them, so nobody sets permissions by hand:
  - an *owner channel*, seen only by the owners and the bot, for the owners' side of every trip;
  - a *trip channel* with exactly the trip's participants, only if the owner invites the sitter to the server. The care thread runs there, and reminders and alerts come with Taken / Snooze / Skip buttons and mention the person they're for, so Discord notifies them. Replies follow the same rules as SMS replies (§8.9). The sitter links their Discord account with a one-time code ([02 §2.17](02-domain-model.md#217-care-threads--channels)), and when the trip ends, the bot removes them from the server.

  A sitter who isn't invited uses the web app, email or text, or messages the bot directly (below). On a server shared with other people, anyone with Discord's Administrator permission can read every channel, so setup names those people before the owner channel is used, and the bot warns the owner if that list changes.
- **Direct messages only.** No server: the owner adds the bot to their own Discord account as a user-installed app, and their one-to-one chat with it is their side of every trip. Sitters can do the same.
  - Linking works either way round. The bot sends a one-time code, or, if Discord won't let it write first, the person sends the bot the code the app shows them, which also opens the chat.
  - Each person's Discord status shows in readiness and on the trip. The owner is told when someone hasn't linked yet, or when Discord turns a message down, so they can talk to the sitter.
  - Until a person's chat works, their reminders and alerts go by the next channel on their list, as they do whenever a channel fails ([02 §2.15](02-domain-model.md#215-notifications--reminders)).
  - Still to test (§8.19): whether the bot can write first and, if not, whether it can keep messaging someone after they've written to it, such as a reminder hours later. If it can't, this setup carries only replies, and reminders and alerts always use another channel.

**Outages.** Nothing outside the house can take over reminders, so:
- The sitter adds the trip's dose times to their phone as alarms, from a calendar file or from a list to set by hand. The times come from the kernel, and a changed dose time sends a new file. An alarm can't tell whether a dose was given, so when one goes off, the sitter checks the offline copy or the care sheet's dose grid first.
- The offline copy, the printed care sheet and the staged door codes work as on a connected install, within the copy's lease.
- An outside monitor, if set up, tells the owner when the house goes quiet.
- Readiness says plainly what isn't covered. A medication trip isn't "ready" until the sitter has added the dose alarms, or the owner accepts the gap after a warning.

**Sign-in and joins.**
- The join check is owner approval, or a code sent through the owner's email account or SMS provider, or by Discord to a sitter already in the household's server.
- Approval requests reach owners by web push, Discord or email.
- New owner devices need a passkey, confirmation on one of that owner's signed-in devices, or a recovery code. There's no Pawsitter-account sign-in.

When standalone mode ships and what it costs are open (Q33, Q34).

## 8.16 Moving between editions

Moving a household between cloud and home comes later (phase 4), but these rules are fixed now so it stays possible:
- **Identity.** User ids are UUIDv7 that Pawsitter ID can adopt unchanged, and revisions reference user ids, never passkey-specific handles.
- **Cutover:**
  - Moves happen only between trips.
  - Secrets are re-wrapped to the destination's key without plaintext leaving the source, after a 24-hour cooling-off that any owner can cancel.
  - The old address stays up for 30 to 90 days as a tombstone: it accepts and forwards queued facts and redirects everything else.
  - Each person gets a re-enrollment link, and printed cards keep working through the join domain.

**Switching a home install between connected and standalone** keeps its data, and can happen between trips. The install's address changes, so passkeys, paired devices and printed cards are set up again.

## 8.17 Packaging and operations at home

- **Runtime.** Node 26 LTS in production for both editions: Active LTS since 2026-10-28, with end of life on 2029-04-30. The official Node binary ships inside each signed package with the app bundle. Single-file executables are deferred: Node's isn't finished and skips Intel Macs, and Bun's are large and need extra flags. Bun 1.4 stays compatible in CI. The kernel runs in worker threads with resource limits ([07 §7.9](07-portable-core.md#79-host-adapters)).
- **Platforms:**
  - **macOS:** a notarized `.pkg`. The server runs as a LaunchDaemon under a dedicated user, with data in `/Library/Application Support/Pawsitter`. Notarization needs the Apple Developer Program (US$99 a year).
  - **Windows:** a signed per-machine installer and a Windows service, with data in `ProgramData`. A firewall rule is added only when a LAN path is enabled, and setup detects a network marked Public.
  - **NAS, Linux, Raspberry Pi:** a multi-arch container image (amd64 and arm64) with a `/data` volume, a healthcheck, and compose and Unraid templates. An admin command, run with `docker exec`, handles recovery, invite QRs and claiming. The host's LAN address comes from configuration, because inside a container the server sees its own internal address.
  - **The tray app** (Tauri, at GA): status, join QRs, approvals, updates, power.
- **The port.** A fixed default that avoids common ones (3000, 5000/5001, 8080, 8123, 32400 and others), with a fallback to the next free port.
- **Support.** A consented diagnostics bundle goes over the Home Link: versions, heartbeats, certificate and backup state, error codes, and no household data. Owners and support also get a per-install health page. Standalone owners can save the bundle and send it themselves.
- **Abuse.** Every connected install is a TLS endpoint with a valid certificate that Pawsitter can't inspect. So:
  - per-install bandwidth and connection quotas by plan;
  - per-install send limits at the push relay and the messaging bridge; the bridge is the metering authority for SMS from home installs, as the model proxy is for AI ([03 §3.10.3](03-core-architecture.md#3103-who-pays));
  - detection of unusual traffic;
  - a takedown and appeal process;
  - the zone categorized with DNS-filter vendors before launch;
  - monitoring of the zone's standing with Safe Browsing and filter lists, and a runbook for when it's flagged: suspend the offending install at the relay, request delisting, and tell affected owners.
- **Uninstalling.** Export, destroy the keys, unpair, clean up DNS, and notify members and sitters.

## 8.18 Phasing

| Phase | Scope |
|---|---|
| **0. Foundations** (now) | **Build:** the monorepo, kernel, core and ports; both stores behind one contract; the test kit running both compositions; sign-in (devices, grants, joins, passkeys, codes, step-up).<br>**Long-lead items:** settle the name (Q20); register the home zone; apply for the Public Suffix List on isolation grounds; request a Let's Encrypt rate-limit override; set up a backup CA.<br>**Fix now:** the identity rules for moving between editions (§8.16). |
| **1. Cloud MVP** | The spec's MVP, plus:<br>- sitters as global users with per-account device grants;<br>- sent, displayed and printed QR joins with a second factor bound to the browser;<br>- linked devices and the security log;<br>- passkeys, the offline copy and web push;<br>- two-way SMS with number pools;<br>- the iOS shell and Android TWA, if they're in the MVP (Q32). |
| **2. Home beta** (internet required) | **Hosts:** the container image and an always-on Mac only, with one sign-in preset.<br>**Services:** the Home Link, relay, DNS and certificates; the push relay, bridge, model proxy and watchdog.<br>**Outage and recovery:** backup reminders and staged door codes; encrypted off-site backup and restore; owners' Pawsitter-account sign-in and remote recovery.<br>**Updates:** signed code and data updates.<br>**Testing:** the same end-to-end suite; passkey tests on real devices with real certificates; outage drills on each beta host (power cut, ISP outage, sleep and wake, a router or DHCP change, a Raspberry Pi without a battery-backed clock, a host on a VPN) that check catch-up, backup reminders, staged door codes and clock trust; and the relay's TLS termination, `node:sqlite` and the power helper re-run on Node 26, since research ran them only on Node 22.23.4 and Bun 1.4.4.<br>**Zone:** a separate, invite-only one. |
| **3. Home GA** | Windows; the tray app; the desktop LAN shortcut; the kiosk; Pawsitter-account sign-in for family and sitters; local models and the owner's own model key; CT monitoring for owners; the production zone once the Public Suffix List entry has shipped; standalone mode, with Tailscale and the owner's own domain, the owner's Discord bot and email, their own backup target and an outside monitor (Q33). |
| **4. Later** | Moving households between editions; WhatsApp, and Pawsitter's own Discord bot for cloud and connected installs (V2); for standalone installs, the owner's own SMS provider, Telegram and Matrix bots, and a private certificate authority; a split-DNS guide; a single-file runtime. |

## 8.19 Open decisions and hypotheses

**For the owner to decide** (in [05](05-open-questions.md)):
- **Q27:** home relay-first.
- **Q28:** the home sign-in defaults, the menu in §8.6.
- **Q29:** outage fallbacks.
- **Q30:** the home-zone domain.
- **Q31:** home pricing.
- **Q32:** whether the iOS shell is in the cloud MVP.
- **Q33:** what standalone mode ships first, and when.
- **Q34:** what standalone mode costs.

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
- Chrome possibly gating top-level navigations to local addresses;
- whether phones keep the alarms in an imported calendar file (iOS Calendar, Google Calendar);
- how reliably Discord's app delivers notifications; whether a user-installed bot can send the first message to someone it shares no server with and, if not, whether it can keep messaging them after they've written to it;
- Tailscale Funnel's bandwidth and connection limits, for photo updates.

Until each is confirmed, its worst-case fallback applies. For example, assume a per-install TWA can't verify its asset links, and send its push through the relay.
