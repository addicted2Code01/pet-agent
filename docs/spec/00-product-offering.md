# 0. Product offering

What we sell, to whom, and why it wins. Built from the [feature research](06-feature-research.md); the features themselves are in [01](01-features.md). "Pawsitter" is a working name: another app already uses it (Q20).

## 0.1 Who it's for

**Households that hand their pets to someone else**: a sitter, a neighbor, family.

The sharpest starting point is **households with a pet on medication or special care**. For them a missed or doubled dose is a real risk, and giving medication is a known source of owner anxiety. About 90 % of professional sitters say they care for or medicate special-needs pets (06 #7).

The people they hand off to (sitters, dog walkers, friends, family) use it free. They get set up by scanning a QR code: no app to install, no password, no sign-up form.

Households that want their data to stay at home can run the **home edition** on their own always-on computer or NAS, with the same experience ([08](08-home-and-cloud.md)).

## 0.2 The promise

> **Hand off your pets' care without the worry.**

Pawsitter keeps your pets' care in one place your family uses every day, and hands it to a sitter in minutes. Your sitter gets a link, not an app: what to do next, where everything is, and whether a dose is safe to give. You see every answer the AI gives them, and one reply corrects it for everyone. You get photo updates as it happens, and their access ends when you're home.

## 0.3 Why it wins

Five hero features that no competitor we found offers in full, plus a daily habit that keeps everything current.

| Hero feature | What the customer gets | Features |
|---|---|---|
| **Safe doses, every time** | Reminders that persist until someone answers. "Can I give it now?" checked against the owner's limits. What to do if a dose is missed or refused, and an instant alert to the owner when it is. | [1.5](01-features.md#15-medications-safety-critical), [1.6](01-features.md#16-care-routines--daily-tasks) |
| **Everything findable** | "Where's the leash?" answered with the spot and a photo. Supplies marked low go straight onto the shopping list. | [1.4](01-features.md#14-items-supplies--inventory) |
| **Access that ends when you're home** | The sitter joins by scanning a QR code, and their access opens and closes with the job. Door codes revealed one at a time, with a log. Vet authorization with a spending limit. | [1.1](01-features.md#11-accounts-people--access), [1.2](01-features.md#12-sites--places), [1.7](01-features.md#17-knowledge-contacts--emergencies) |
| **Ready in 10 minutes** | Paste the note you already leave for sitters; AI drafts the setup and you confirm each entry. | [1.12](01-features.md#112-setup--onboarding) |
| **You stay in the loop** | Every answer the AI gives your sitter appears in the trip's care thread, whichever channel they asked on. Reply from any channel to correct it: your words are pinned for the sitter at once, and one tap fixes the plan everywhere. You can always see why it answered as it did. | [1.14](01-features.md#114-care-thread--ai-oversight) |

**The everyday hook.** Sitter apps get used a few times a year, so their information goes stale. Pawsitter's reminders and shared log are useful every day ("did anyone feed the dog?"), so the family keeps it current and it's ready the moment a sitter is needed. A whole category of small apps exists only to answer that question (06 #2), which shows the demand.

## 0.4 Table stakes we match

Customers expect these from any app in this space. All are in the MVP:

- Reminders that reliably fire, with one-tap Taken / Snooze / Skip (06 #1)
- A shared log of who did what, which clears everyone's reminder (06 #2)
- Photo updates and reports, pushed as they happen (06 #3)
- A care guide the sitter opens from a link or QR code, with no app, password or sign-up form (06 #4)
- A complete care sheet and emergency card (06 #5)
- A today checklist (06 #9)
- Flexible doses: ½ tablets, syringes, every N hours, tapering (06 #11)

## 0.5 Core journeys

1. **Set up (10 minutes).** Pick a template or paste your existing care note, then confirm the drafted routines, medications and contacts. Snap photos of where the food, leash and medicine live. Invite your family. ([1.12](01-features.md#112-setup--onboarding))
2. **Every day.** Family members get reminders. Whoever feeds or medicates taps Done, and everyone else's reminder clears. Supplies marked low go on the shopping list. ([1.6](01-features.md#16-care-routines--daily-tasks), [1.4](01-features.md#14-items-supplies--inventory))
3. **Going away.** Create a trip: dates, sitter, pets and vet authorization. A readiness check flags gaps, such as no emergency vet, a medication without "if missed" instructions, or supplies running low. Send the sitter a join link, or show them the QR code when they visit. ([1.1](01-features.md#11-accounts-people--access), [1.10](01-features.md#110-platform))
4. **During the stay.** The sitter opens the link and sees today's checklist, can-I-give-it, where things are and the emergency card, with an offline copy. Reminders reach them by SMS or push. Their questions to the AI, and its answers, appear in the care thread, where the owner can correct them. The owner gets photo updates, and an alert at once if a dose is refused or missed. ([1.9](01-features.md#19-interfaces-adapters-not-core), [1.8](01-features.md#18-activity-reporting--notifications), [1.14](01-features.md#114-care-thread--ai-oversight))
5. **Coming home.** Tap "I'm home". The sitter's access closes, both get the stay summary, and the shared log carries on. ([1.1](01-features.md#11-accounts-people--access), [1.8](01-features.md#18-activity-reporting--notifications))

## 0.6 How it compares

By category, as each product advertises itself ([06](06-feature-research.md)). ✓ = offers it · ◐ = partly · – = not found in our research.

| Need | Care-guide apps (Pawzfolio, Meet My Pet, Wagabond) | Medication apps (Muzzly, PetPill, PokiPaw) | Family loggers (Hound, Paw Clock) | Sitter platforms (Rover, Time To Pet, Pet Sitter Plus) | AI pet apps (Petcube, My Pets AI) | Pawsitter |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Care guide by link, no app for the sitter | ✓ | – | – | – | – | ✓ |
| Reminders and a shared log | – | ✓ | ✓ | – | ◐ | ✓ |
| Warns before a too-soon or double dose | – | – | – | – | – | ✓ |
| Where things are kept, with photos | – | – | – | ◐ | – | ✓ |
| Access that expires; codes revealed with a log | ◐ | – | – | ◐ | – | ✓ |
| Photo updates during a stay | ◐ | – | – | ✓ | – | ✓ |
| Emergency contacts and vet authorization | ◐ | – | – | – | – | ✓ |
| Setup from the notes you already have | – | – | – | – | – | ✓ |
| AI answers from your own household's data | – | – | – | – | ◐ | ✓ |
| Owner sees and can correct what the AI tells the sitter | – | – | – | – | – | ✓ |

**Price is a wedge too.** Competitors charge to share: Pawzfolio's $4.99/month tier is what unlocks sharing, and Muzzly and PetPill put sharing in paid tiers. Sharing with a sitter is free in Pawsitter (§0.7).

**What we don't do:** find sitters, run general-purpose chat (the care thread is only about care), offer vet telehealth or diagnose. Rover and Wag own sitter-finding; we make any sitter better at the job ([1.13](01-features.md#113-deliberately-not-building)).

## 0.7 Packaging (proposal)

Principles, from the complaints in [06 §6.5](06-feature-research.md#65-complaints-and-pitfalls): sharing with a sitter is always free; safety features are never paywalled; features are never taken away from existing users; cancelling takes one tap.

| | Free | Plus |
|---|---|---|
| Owned homes (the vet, boarding and other external places are unlimited) | 1 | Several |
| Pets, family members, sitters | Unlimited | Unlimited |
| Reminders, shared log, dose safety, emergency card, care sheet | ✓ | ✓ |
| "Where is it?" and supply levels | ✓ | ✓ |
| Photo updates and stay summaries | ✓, recent history | ✓, full history |
| SMS reminders for sitters | Small monthly allowance | Larger allowance |
| AI care-note import | Onboarding credits | ✓ |
| AI assistant | – | Monthly allotment |
| Edge node: local model, home-held keys | – | V2 |

**Home edition** (from the home beta, [08](08-home-and-cloud.md)). Household data stays on the owner's computer, and it still uses Pawsitter's companion services.
- **Free:** sitter access through the relay; reminders, push and the watchdog; backup reminders and staged door codes for outages; encrypted off-site backup of the structured data. Sharing with a sitter is always free, and safety is never paywalled.
- **Plus:** relay bandwidth above a cap (photos), media backup, and the hosted assistant.

Exact limits are open (Q31).

**Price** is open (Q19). Anchors: Pawzfolio's sharing tier is $4.99/month; Petcube charges $9.99/month for its AI assistant and vet chat; the PawSitter business app charges $7.99/month. One option to test: Plus at $4.99/month or about $40/year, which is no more than the cheapest paid sharing tier and includes the AI assistant.

## 0.8 MVP scope and success measures

The MVP is everything marked MVP in [01](01-features.md), organized around the five journeys above. Proposed measures for the beta:

| Measure | Proposed target | Why |
|---|---|---|
| Median time from sign-up to a sitter-ready guide | Under 10 minutes | Setup effort decides whether anyone gets value (06 #6) |
| Reminders delivered within a minute of their time | 99.5 % or better | Unreliable reminders are the category's top complaint (06 #1) |
| Medication doses during stays logged within their window | 95 % or better | The safety outcome we promise |
| Too-soon or double doses caught by the dose check | Count and report | Proof the safety promise works, and a number to market with |
| Sitters who say the guide had everything they needed (one tap at handback) | 90 % or better | The handoff is the product |
| AI answers corrected by owners | Track the rate; review causes with the owner's permission | Each correction shows where the records or the model need fixing |
| New households that get a sitter joined within 30 days | Set after the beta | Activation |
| Households active weekly between trips | Set after the beta | The everyday hook |

Before locking pricing or investing beyond MVP in "where is it?", run the interviews and hands-on trials in [06 §6.8](06-feature-research.md#68-what-to-validate-next).
