# 9. Capabilities and delivery options

What the platform has to do, the technologies that could deliver each part, and the shapes a first release (V1) could take. This document is for making choices. Once one is made, it moves into the document that owns it and into [05](05-open-questions.md).

Facts were checked on 2026-11-07, with sources linked in each section's notes. Prices change, and hardware prices are changing fastest.

## 9.1 How to read the tables

- Each capability has one table, with a row per option.
- **They do** is what the owner and the sitter have to do. **Our effort** is what we build and then run. Effort is *low*, *medium* or *high*.
- **Cost** is in US dollars at small scale.
- **Verdict** is *V1*, *Later* or *No*. A verdict is a recommendation until a question in 05 settles it.

## 9.2 The capability map

Most of the product is core logic that's built whatever we choose here: records, `can_administer`, routines, the care thread, corrections, history. These are the capabilities where the delivery technology is a real choice.

| Capability | What depends on it | Needed in V1 | Status |
|---|---|---|---|
| Where the core and data run | Everything | Yes: the cloud | Decided: cloud first; home in V2 (Q2) |
| The owner's and family's app | Setup, reminders, alerts, corrections, approvals | Yes | Open (Q21, Q32); §9.4 |
| The sitter's view | Today's checklist, can-I-give-it, where-is, the emergency card, the offline copy | Yes | Decided: a web link and QR code, no install (Q11) |
| Reaching people | Reminders that persist, dose alerts, photo updates, reports | Yes | Partly decided (Q15, Q24); §9.3 |
| Conversations on outside channels | The care thread outside the app | App and web in V1 | MVP: app, web and two-way SMS (Q24); §9.3 |
| Confirming a join | Sitter joins and step-ups | Yes | Decided: a code by SMS or email, or owner approval ([08 §8.7](08-home-and-cloud.md#87-joining-by-qr)) |
| Media | Photo updates, evidence, voice messages | Photos | Open (Q35) |
| AI | Care-note import, the assistant, reports | Yes (hero features) | Decided: pluggable, hosted by default (Q3); §9.7 |
| Remote access to a home install | The home edition | No | Open (Q27); §9.5 |
| Packaging a home install | The home edition | No | Open (Q37); §9.6 |
| Backups and updates | Trust and safety | Cloud only | Cloud is ours to run; home in [08](08-home-and-cloud.md) |
| Billing | The Plus plan | No | V2 ([01 §1.10](01-features.md#110-platform)) |

## 9.3 Reaching people and holding conversations

| Channel | They do | Our effort | Cost (US) | Good at | Weak at | Verdict |
|---|---|---|---|---|---|---|
| Native app push | Install the app | High: app review, two platforms | Free | Taken / Snooze / Skip on the lock screen; time-sensitive alerts get through Focus | Sitters won't install an app | V1 for owners if Q32 says yes; never required of sitters |
| Web push | Allow notifications; on iPhone, add the site to the Home Screen first | Low to medium | Free | No app; payloads encrypted to the browser | No notification buttons on iPhone or in Safari | V1 |
| SMS and MMS | Nothing beyond consent at join | Low, after carrier registration | $0.0083 per segment plus $0.0035–0.005 in carrier fees; MMS $0.022 | Reaches 98% of US adults; two-way replies | No buttons, so numbered replies plus a link; unknown-sender filtering | V1: sitters' medication reminders, replies, join codes |
| RCS business messaging | Nothing, on capable phones | Medium: approval per carrier, 4–6+ weeks | About SMS, plus up to $0.0062; $600+ to onboard | Buttons, read receipts and rich media, falling back to SMS | Approval lead time; carrier support varies | Later: a fast follow on the same message layer |
| Email | Nothing | Low | $0.10 per 1,000 | Codes, daily reports, stay summaries, fallback | Slow and filtered; links only | V1 |
| WhatsApp | Both have the app and an account | Medium: Meta business verification | About $0.008 per message | Reply buttons, voice notes, media; dominant outside the US | 32–34% of US adults; templates outside a 24-hour window; Meta reads Cloud API messages; rules on AI assistants | Later: first for markets outside the US |
| Telegram | Both have the app; one tap on a link from the QR | Low | Free | Buttons, voice notes, no fees | Little US use; a bot can't start a chat | Later: an option for standalone installs |
| Discord | An account; a server or a user-installed app ([08 §8.15](08-home-and-cloud.md#815-standalone-mode)) | Low to medium | Free | Buttons, voice, the owner's own bot | Little household use; direct messages should start with the person | Later: standalone installs (V2) |
| Slack | A workspace; the sitter needs an invite | Medium | Shared channels need paid plans; free plans show 90 days | Professional sitters' businesses | Households don't use it | No; revisit for professional sitters |
| Facebook Messenger | A Facebook account; the person writes first | Medium: app review | Free | Quick replies | 24-hour window; review | No |
| Signal | — | — | — | The best privacy | No bot API; its terms ban automation | No |
| Apple Messages for Business | An iPhone; the person writes first | High: an approved provider | Provider fees | Rich pickers | The business can't start; heavy approval | No |
| Automated voice call | A phone, and consent beforehand | Low to medium | About $0.014 per minute | Wakes someone for a missed dose; keypad answers | Few people answer unknown numbers; consent rules | Later: owner escalation only, with consent at setup |

**Notes.**
- **SMS needs registration before the first message.** That means 10DLC (brand $4.50 or $46, campaign vetting $15, then $1.50–$10 a month) or toll-free verification. New toll-free verifications have needed a business tax ID since February 2026, except for sole proprietors. Start now; it's a long-lead item. ([Twilio pricing](https://www.twilio.com/en-us/sms/pricing/us), [10DLC fees](https://support.twilio.com/hc/en-us/articles/1260803965530-Pricing-and-Fees-for-A2P-10DLC-Service), [toll-free change](https://www.twilio.com/en-us/changelog/business-registration-numbers-required-for-toll-free-messaging-p))
- **Phones hide unknown senders.** iOS 26 can screen texts from unknown senders, and few people answer calls from unknown numbers. So the join flow asks the sitter, and setup asks the owner, to save Pawsitter's contact card. ([Apple](https://support.apple.com/en-us/125068), [Pew](https://www.pewresearch.org/short-reads/2020/12/14/most-americans-dont-answer-cellphone-calls-from-unknown-numbers/))
- **On iPhone, only a native app puts buttons in a notification.** Web push there needs a Home Screen install and shows no action buttons. Buttons inside a message need RCS or WhatsApp. ([WebKit](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/), [caniuse](https://caniuse.com/mdn-api_serviceworkerregistration_shownotification_options_actions_parameter))
- **RCS reaches iPhones** from iOS 18.1 where the carrier enables it, with up to 11 suggested replies per message. Approval takes 4–6+ weeks per brand with no promised turnaround, and weak proof of opt-in is the most common reason for rejection. ([Twilio](https://www.twilio.com/en-us/blog/insights/trends/rcs-business-messaging-apple-update), [Google](https://developers.google.com/business-communications/rcs-business-messaging/guides/build/messages/send), [onboarding](https://help.twilio.com/articles/49174994355355-RCS-Compliance-Onboarding-Guide))
- **WhatsApp:**
  - It has charged per message since July 2025. Since October 2026, free-form replies are free only for the first 1,000 a month per number.
  - New accounts can reach 250 people a day until they're verified.
  - Meta has barred general-purpose AI assistants since January 2026. Ours answers only about the household's care, but confirm that before building.

  ([pricing](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing), [non-template messages](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/non-template-messages), [limits](https://developers.facebook.com/documentation/business-messaging/whatsapp/messaging-limits), [TechCrunch](https://techcrunch.com/2025/10/18/whatssapp-changes-its-terms-to-bar-general-purpose-chatbots-from-its-platform/), [Pew](https://www.pewresearch.org/internet/2025/11/20/americans-social-media-use-2025/))
- **Telegram bots can't start a chat,** but the join QR can open `t.me/<bot>?start=<token>`, so the sitter's first tap links their account. Bot messages are free up to 30 a second. ([Telegram](https://core.telegram.org/bots), [FAQ](https://core.telegram.org/bots/faq))
- **An App Clip** could give a sitter native notifications from the QR code with no install, but only for a limited time. Apple's own WWDC sessions disagree on the limit (8 hours, 24 hours, or up to a week), so test it before relying on it. ([WWDC20](https://developer.apple.com/videos/play/wwdc2020/10120/), [WWDC21](https://developer.apple.com/videos/play/wwdc2021/10013/))
- **Voice calls with recorded or synthetic voices need prior consent** under US rules, so the owner agrees at setup, and calls go only to owners and backup contacts. ([FCC](https://www.fcc.gov/document/fcc-makes-ai-generated-voices-robocalls-illegal))

## 9.4 The owner's app

| Option | Our effort | Gets | Gives up | Verdict |
|---|---|---|---|---|
| The web app only, installable | Low | One codebase; web push | On iPhone, push needs a Home Screen install and has no notification buttons | The V1 floor |
| Thin native shells: an iOS app with a notification extension, and an Android Trusted Web Activity | Medium: app review, $99 a year for Apple | Taken / Snooze / Skip on the iPhone lock screen; time-sensitive reminders; a store listing | A second release process | V1 if Q32 says yes (recommended) |
| Fully native apps | High | The most polish | Two more codebases to keep in step | No |

## 9.5 Remote access for home installs

V1 is cloud only, so it doesn't need this. It decides how the home edition (V2) works while the owner is away and the sitter is on mobile data.

| Option | Owner does | Sitter does | Cost | Who can see traffic | Our effort | Weak at | Verdict |
|---|---|---|---|---|---|---|---|
| Our own relay, passing encrypted traffic through by name, as Nabu Casa does for Home Assistant | Installs and signs in | Opens the link | Servers and bandwidth are cheap; staff time dominates | Names, addresses, timing and volume; keys stay at home | High: the relay, the tunnel client, DNS, certificates and an abuse desk | Certificate limits, an uncertain Public Suffix List entry, and one bad install can get the whole zone flagged | V2: connected installs ([08 §8.4](08-home-and-cloud.md#84-https-for-home-installs)) |
| Tailscale Funnel | Installs Tailscale on the home machine and turns on HTTPS and Funnel | Opens the link | Free | Nobody: TLS ends at home | Low | Still in beta; only `*.ts.net` names and three ports; unpublished bandwidth limits | V2: standalone installs, and a candidate for the home beta |
| Tailscale as a private network | Installs Tailscale on every device | Would need Tailscale and an account too | Free for up to 6 users, for personal use | Nobody | Low | Sitters can't be asked to install it | V2: owners' and family devices in standalone mode |
| Cloudflare Tunnel, with Cloudflare Access | Moves their domain's DNS to Cloudflare and runs its connector | Opens the link; with Access, also types an emailed PIN | A domain; the tunnel is free | Cloudflare decrypts everything, door codes included | Low to medium | 100 MB upload limit; terms on video and large files | Later: a standalone option, with a plain privacy warning |
| ngrok | Signs up and runs its agent | Opens the link; the free plan shows a warning page first | $0–$20+ a month | ngrok (not verified) | Low | 1 GB a month free; own domains only from $20 a month | No |
| Port forwarding with dynamic DNS | Sets up the router, DNS and certificates | Opens the link | About $0, plus a domain | Nobody in the path | Medium | Impossible behind carrier-grade NAT; exposes the machine to internet scans | Later: an advanced standalone option |
| A tunnel through the owner's own server (frp, rathole, Pangolin) | Rents a server, sets DNS, runs the tunnel | Opens the link | About $4–$7 a month | The server's host, unless traffic passes through encrypted | Medium | Technical setup; one more server to keep up | Later: an advanced standalone option |
| ZeroTier, NetBird, Headscale | Installs a client everywhere | Installs a client | Free tiers | Varies | Medium | Sitters would have to install an app | No |

**Notes.**
- **Inbound connections can't be the default.** Starlink's default carrier-grade NAT blocks inbound traffic, and fixed wireless is about 14% of US home broadband. So a home install has to dial out, to our relay or to Funnel. ([Starlink](https://starlink.com/support/article/1192f3ef-2a17-31d9-261a-a59d215629f4), [ComSoc](https://techblog.comsoc.org/2026/08/27/ookla-u-s-fixed-wireless-access-crosses-17-million-connections-as-adoption-shifts-from-rural-to-urban/))
- **"The sitter installs nothing" leaves only public addresses:** our relay, Funnel, Cloudflare, ngrok, the owner's own server, or port forwarding. Sharing a Tailscale machine needs the sitter's own account and app. ([Tailscale sharing](https://tailscale.com/docs/features/sharing))
- **The name is effectively permanent.** Passkeys belong to the site's domain. Moving an install from `*.ts.net` to our zone later means re-enrolling passkeys and reprinting cards ([08 §8.16](08-home-and-cloud.md#816-moving-between-editions)), so decide the naming before the home beta. ([web.dev](https://web.dev/articles/webauthn-rp-id))
- **Our relay is an ongoing operation:**
  - Let's Encrypt allows 50 new certificates a week per registered domain, unless it grants an override, which takes a few weeks. Without one, that's about 2,600 new installs a year.
  - The Public Suffix List says it will likely decline small or beta projects.
  - Certificate lifetimes drop to 64 days in February 2027 and 45 days in February 2028.
  - In October 2025, one flagged subdomain got all of `*.immich.cloud` marked dangerous.

  Nabu Casa runs the same design for Home Assistant at $6.50 a month. ([rate limits](https://letsencrypt.org/docs/rate-limits/), [PSL guidelines](https://github.com/publicsuffix/list/wiki/Guidelines), [64-day](https://letsencrypt.org/2026/10/07/64-day-certs), [45-day](https://letsencrypt.org/2025/12/02/from-90-to-45), [Immich](https://immich.app/blog/google-flags-immich-as-dangerous), [Nabu Casa](https://support.nabucasa.com/hc/en-us/articles/25619268678557-Remote-access-Deep-dive), [price](https://support.nabucasa.com/hc/en-us/articles/26179687501341-How-much-does-a-Home-Assistant-Cloud-subscription-cost))
- **Tailscale Funnel** is still in beta. It serves only ports 443, 8443 and 10000 on `*.ts.net` names, with bandwidth limits Tailscale doesn't publish. The free Personal plan covers 6 users. ([Funnel](https://tailscale.com/docs/features/tailscale-funnel), [pricing](https://tailscale.com/pricing))
- **Tailscale can be built in.** Its `tsnet` library embeds a Tailscale node, certificates included, in a Go program. A small helper could give a home install Funnel without a separate Tailscale install; the owner still signs in to Tailscale once. ([tsnet](https://tailscale.com/docs/reference/tsnet-server-api))
- **Cloudflare decrypts traffic at its edge,** and its free and Pro plans limit uploads to 100 MB. ([SSL modes](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/), [413](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/4xx-client-error/error-413/))
- **Precedents:**
  - Plex falls back to a relay capped at 2 Mbps.
  - Synology QuickConnect relays as a last resort, with noticeable delay.
  - Umbrel and Immich point owners to Tailscale.
  - Jellyfin has no relay.

  ([Plex](https://support.plex.tv/articles/216766168-accessing-a-server-through-relay/), [Synology](https://kb.synology.com/en-sg/WP/Synology_QuickConnect_White_Paper/4), [Umbrel](https://umbrel.com/support/basics/remote-access), [Immich](https://docs.immich.app/guides/remote-access/), [Jellyfin](https://jellyfin.org/docs/general/post-install/networking/))

## 9.6 Packaging home installs

| Option | Owner does | Owner pays | Our effort | Updates | Main risk | Verdict |
|---|---|---|---|---|---|---|
| A Home Assistant app (formerly "add-on") | Adds our repository's address in Home Assistant, then installs | Nothing extra, on Home Assistant OS | Low to medium: one multi-arch image and a repository | Owners can turn on auto-update per app | Only Home Assistant users; its supervisor no longer checks image signatures | V2: the first home channel |
| A container on a NAS (Synology, QNAP, Unraid, TrueNAS) | Creates a project from our compose file | Nothing extra; Unraid licences are $49–$249 | Low to medium: one image, about five listings | The owner clicks Update; nothing updates on its own | Skipped security updates; a technical audience | V2, with update prompts in the app |
| Native installers for Mac and Windows | Runs an installer and keeps the computer on | Nothing extra | Medium to high: signing ($99 a year for Apple, $9.99 a month for Microsoft's signing service), a service, an updater | Our signed updater | Sleep and laptops; Windows warnings | V2: Mac in the home beta, Windows at GA ([08](08-home-and-cloud.md)) |
| An OS image for a Raspberry Pi the owner buys | Buys the parts and writes the image with Raspberry Pi Imager | About $150–$235 in parts | Medium to high: an OS image with A/B updates | Our signed A/B updates | Hardware variety; support load | Later |
| A box we sell, preloaded | Plugs it into the router and scans its QR code | Similar products cost $199–$899 | High: we become a hardware maker | Our signed A/B updates | Certification, returns and stock; memory-driven price swings | Later: once the software has proven itself |
| A one-click server in the owner's own cloud account | Opens a cloud account and deploys | About $2–$6 a month plus storage | Low to medium: a template per provider | Redeploying a new image | The data leaves the home; the owner runs a server | Later: really a third edition |
| An app on another home platform (Umbrel, Start9, Synology Package Center) | One click on that platform | That platform's cost | Medium per platform: review | That platform's store | Its rules and review times | Later |

**Notes.**
- **Home Assistant is the largest ready-made channel,** with over 2 million homes. Owners add a repository by its address and can turn on auto-update per app. Apps need Home Assistant OS, since its other install types lost support in 2025.12. ([Open Home Foundation](https://www.openhomefoundation.org/blog/the-first-of-many-our-2025-annual-report/), [publishing](https://developers.home-assistant.io/docs/apps/publishing/), [deprecation](https://www.home-assistant.io/blog/2025/05/22/deprecating-core-and-supervised-installation-methods-and-32-bit-systems/))
- **Most NAS platforms don't update containers by themselves.** On Synology and TrueNAS the owner clicks Update, and Unraid needs a plugin. Watchtower, the usual auto-updater, was archived in December 2025. So a home install has to check for updates itself, prompt the owner, and verify signatures. ([Synology](https://kb.synology.com/en-global/DSM/help/ContainerManager/docker_image?version=7), [TrueNAS](https://apps.truenas.com/managing-apps/managing-installed-apps/), [Linuxiac](https://linuxiac.com/docker-update-tool-watchtower-reaches-end-of-maintenance/))
- **Selling a box makes us the manufacturer, even on a pre-certified board:**
  - FCC Part 15B testing and labelling in the US;
  - the EU's radio cybersecurity rules, applied since August 2025;
  - UK rules against default passwords;
  - EU two-year guarantees and 14-day returns.

  ([Raspberry Pi e-label](https://pip-assets.raspberrypi.com/categories/1003-compliance-information/documents/RP-006510-DS-1-Raspberry%20Pi%205%20e-label.pdf), [FCC](https://fcc.gov/sites/default/files/32-KDB-996369-Modules-TCB_Oct_2023.pdf), [EC](https://single-market-economy.ec.europa.eu/sectors/electrical-and-electronic-engineering-industries-eei/radio-equipment-directive-red_en), [GOV.UK](https://www.gov.uk/guidance/regulations-consumer-connectable-product-security))
- **Hardware prices are volatile:**
  - Home Assistant Green went from $99 to $199 in January 2026 because of memory costs.
  - A Raspberry Pi 5 with 4 GB now costs $110.
  - Firewalla paused some sales for lack of memory chips.

  A box we sell would carry that risk. ([Nabu Casa](https://www.nabucasa.com/news/2026-01-08-green-pricing-change/), [Raspberry Pi](https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-008348-DS-6-raspberry-pi-5-product-brief.pdf), [Firewalla](https://firewalla.com/collections/all))
- **Similar boxes:** Home Assistant Green ($199), Umbrel Home (about $399–$599; sources disagree), Start9 Server One ($899). umbrelOS is licensed for non-commercial use only, so we couldn't sell boxes running it without Umbrel's permission. ([Umbrel](https://umbrel.com/legal/umbrelos/tos), [Start9](https://store.start9.com/products/server-one))
- **Updates on a box or OS image:** RAUC is free and uses signed A/B slots. Hosted Mender costs $34 a month for up to 50 devices. ([RAUC](https://github.com/rauc/rauc/blob/master/docs/basic.rst), [Mender](https://mender.io/pricing/plans))
- **SQLite survives a power cut** only if the storage honours sync requests, and some flash storage doesn't. A box or OS image would need storage chosen for that. ([SQLite](https://www.sqlite.org/howtocorrupt.html))
- **The EU's Cyber Resilience Act already applies to software, however it's packaged.** Since 11 September 2026, makers must report actively exploited vulnerabilities within 24 hours. The full obligations start in December 2027. ([EC](https://digital-strategy.ec.europa.eu/en/policies/cra-reporting))

## 9.7 AI

| Option | Our effort | Cost | Good at | Weak at | Verdict |
|---|---|---|---|---|---|
| A hosted model through the `ModelGateway` | Medium: metering and routing are built anyway ([03 §3.10](03-core-architecture.md#310-ai-usage-metering)) | Per call, metered against each account's allotment | Care-note import, the assistant, reports | Only `normal` data may be sent | V1 (decided, Q3) |
| A local model on the owner's hardware | Medium: an edge node or home install | The owner's electricity | `private` data stays home | Slower and weaker on small machines | Later (V2) |
| The owner's own provider key | Low | Billed to the owner | No allotment needed | Support across providers | Later |
| No AI | None | None | Every safety feature still works (principle 2) | No import, assistant or written reports | The fallback when the allotment runs out |

## 9.8 Candidate V1 shapes

Each shape keeps every safety feature. They differ in how people are reached, and how much we build before the first households use it.

**A. Cloud, web first (the leanest).**
- **Ships:**
  - the cloud only;
  - the owner's and family's web app, installable, with web push;
  - the sitter's web link and QR code;
  - SMS for sitters' medication reminders, replies and join codes;
  - email for codes, reports and fallback;
  - the care-note import and the assistant, in the app and on the web;
  - photos.
- **Gives up:**
  - Taken / Snooze / Skip on the iPhone lock screen, so a reminder opens the task, where Taken is one tap;
  - outside chat channels;
  - the home edition.
- **Long-lead items:** SMS registration, and the email domain's sender records.
- **Main risk:** iPhone owners have to add the app to their Home Screen before they get push.

**B. A, plus thin native shells.**
- **Adds:**
  - the iOS shell with lock-screen buttons and time-sensitive reminders;
  - the Android Trusted Web Activity.
- **Costs:** app review, the Apple Developer Program, and a second release process. Starting the iOS shell early shortens the wait.

**C. Home first.**
- **Ships:** a home install as the first product, through a Home Assistant app or a box we sell.
- **Costs:** all before the first household:
  - remote access, through Tailscale Funnel (the fastest start, but in beta) or our own relay (an ongoing operation);
  - signed updates and the outage plan;
  - support for owners' machines.

  Selling a box adds the hardware business on top.
- **Fits:** a local-first story for a technical audience. It's the slowest way to a reliable product for everyone else.

**Recommendation:**
- **V1:** shape A.
- **Next:** B's iOS shell, as soon as the beta shows owners miss lock-screen buttons. Start SMS registration now, and add RCS as a fast follow.
- **Home edition (V2):** a Home Assistant app first, then NAS containers and the Mac installer. A box we sell is the last step, once the software is proven, ideally with a hardware partner.

These shapes are about delivery. The MVP feature list in [01](01-features.md) is large too, and a separate pass can cut it to a V1 core.

## 9.9 Decisions this document feeds

- **Q36: the V1 shape** (§9.8). Everything else follows from it.
- **Q32:** whether the iOS shell is in V1 (§9.4).
- **Q24:** confirm SMS for V1, and RCS as the fast follow (§9.3).
- **Q27:** remote access for home installs (§9.5).
- **Q37:** how the home edition ships first, and whether we ever sell a box (§9.6).
