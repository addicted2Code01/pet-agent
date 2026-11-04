# 5. Open questions

Decisions needed before building, roughly in order of how much they shape the core. Each has a recommendation; mark it ✅ when decided.

## Product & market

**Q1. Who is the first paying customer?** ✅
*Decided:* pet owners (households) who share access with sitters, friends and family. Professional sitters can follow as a tier without a rewrite, because one user can already belong to many accounts. Clinics and boarding facilities need cross-account sharing, so they come later.

**Q2. Cloud, local-first, or hybrid?** ✅
*Decided:* cloud first, with the location of each part configurable. The model, vision, media files and secret keys can each run in the cloud or on the owner's hardware (through an edge node), chosen per account and routed by data sensitivity. Each account's structured data still has exactly one home. See [03 §3.9](03-core-architecture.md#39-deployment-and-placement).

**Q3. Does the AI assistant run locally or hosted?** ✅
*Decided:* pluggable. The cloud product defaults to a hosted model that only sees `normal` data; a local model on the owner's edge node may see `private` data. Hosted usage is metered against a per-account AI allotment. See [03 §3.10](03-core-architecture.md#310-ai-usage-metering).

## Domain modeling

**Q4. Can items belong to several pets, or to none?** Proposed: `pet_ids[]`, possibly empty. ✅ unless you see a reason otherwise.

**Q5. How fine-grained should places be?** The tree allows any depth. Should the UI suggest a fixed set of levels (Room › Spot › Container) to keep data clean?

*Recommendation:* any depth in the core; the UI suggests three levels.

**Q6. Do we track consumables per place?** Wipes in the kitchen *and* the bathroom = two stock levels. Proposed: yes (`StockLevel` is per item per place).

**Q7. Should pets have room-level location, or just site?** Proposed: site required, place optional ("Biscuit is in the bathtub during storms" is useful).

**Q8. Multiple pets sharing a routine** (feed both cats at 8 am): one task for both, or one per pet?

*Recommendation:* one task listing both pets, with the option to record a per-pet exception ("Sonic didn't eat").

**Q9. Medication safety scope.** Enforce only the owner's limits (interval, max per window, not-before)? Or also flag known drug-species warnings, like the Maropitant box saying "dogs only" for a cat?

*Recommendation:* owner limits only in MVP; consider a reference-data port for warnings later, clearly labeled.

**Q10. Food as items or as a separate diet model?** Proposed: food is an item (consumable), and amounts live in feeding routines. Allergies and restrictions are knowledge entries with `kind = rule` on the pet.

## Access & collaboration

**Q11. Do caregivers need an account to help?** ✅
*Decided (revised 2026-11-04):* no app, no password and no sign-up form, but every sitter becomes a lightweight **user** when they join. Joining is by a QR code the owner sends, shows or prints, confirmed by a code to the contact the owner entered or by the owner's approval. Access is bounded by the trip and revocable at once, and every action is attributed to a person and device. Cloud sitters have one login across households; home sitters are local to the install.

This replaces the earlier no-account sitter link. Every care-guide competitor still leads with "no app" ([06 #4](06-feature-research.md#63-ranked-features)), and that promise holds. See [08 §8.5](08-home-and-cloud.md#85-identity-and-sign-in) to [§8.8](08-home-and-cloud.md#88-revocation-ending-and-late-doses) and [04 §4.2](04-permissions-privacy.md#42-time-boxed-access).

**Q12. Can the owner see a caregiver's location** (check-in geofence)? It's useful for pros and sensitive for friends.

*Recommendation:* opt-in per engagement, V2.

## Technical

**Q13. Core language.** ✅
*Decided:* TypeScript compiled to plain JavaScript, so one kernel build runs on the server, the owner's machine, browsers, the app shells, and later on JavaScriptCore, Hermes and .NET engines. Hosts may supply capabilities through shims but nothing that decides a result; time-zone data, recurrence and decimals are bundled in the kernel. See [07](07-portable-core.md).

**Q14. Offline support in MVP?** ✅
*Decided:* partly. The sitter's phone keeps a read-only offline copy of the care guide and emergency card, and task completions queue while offline. Full offline editing and sync come in V2. Ids, versions and idempotent commands are designed for it from day one.

**Q15. Notifications in MVP?** ✅
*Decided:* yes, and reminders are the top-ranked feature ([06 #1](06-feature-research.md#63-ranked-features)). Push with email as backup for persistent reminders and escalation, refused or missed doses, urgent incidents, photo updates and reports. Sitters without the app get medication reminders by SMS.

## Placement & AI usage

**Q16. Edge node in MVP or V2?**

*Recommendation:* V2. The MVP builds the seams it needs ([03 §3.9.5](03-core-architecture.md#395-rules-the-core-follows-from-day-one)), so adding it later is one adapter plus configuration. Pull it into MVP only if a local model is a launch requirement.

**Q17. What unit do customers see their allotment in:** credits, tokens or money?

*Recommendation:* show a simple meter ("62 % of this month's AI used, resets Nov 15"), backed by credits whose rates track provider cost. A pricier model then uses the allotment faster, and margins hold when provider prices change. Rolling token and request limits are there only to stop abuse.

**Q18. What happens when the allotment runs out?**

*Recommendation:* in MVP, hosted AI stops until the period resets and every care feature keeps working. In V2, fall back to the owner's edge node or a cheaper model, and sell top-ups. Never bill overage without an opt-in.

**Q19. How big is each plan's allotment?**

*Recommendation:* measure first. Run the beta with generous limits, record the cost per active household for four weeks, then set the standard allotment near the 90th percentile of monthly use.

## From the feature research

**Q20. Product name.** "PawSitter: Pet Boarding & Care" is already on the App Store, at pawsitter.app.

*Recommendation:* choose a new name before buying domains or building branding, and run a trademark search on the shortlist.

**Q21. How do owners get reliable push: a native app or a PWA?** Reminders are the most important feature, and on iPhone, web push works only after the user adds the site to their home screen.

*Recommendation:* a thin native shell around the web app for owners and family (one codebase, reliable push), and the no-install web link with SMS reminders for sitters. With the core in TypeScript (Q13), the shell runs the same kernel as the web app.

## Care threads

**Q22. Which AI answers should notify the owner right away?** Every answer is visible in the care thread as it happens, but a notification for each one would be noise.

*Recommendation:* notify at once for answers about medication, health or incidents. Show the rest in the thread and the daily report. Per trip, the owner can switch to "notify me of every answer".

**Q23. Should an owner be able to hold the AI's medication answers for approval?** For a new sitter or a risky medication, an owner may want to see an answer before the sitter does.

*Recommendation:* yes, in V2, as a per-trip "review mode" for medication answers. If the owner doesn't respond within a set time, the sitter sees the computed answer and the owner's written instructions, never an unreviewed AI paraphrase.

**Q24. Which channels ship first?** ✅
*Decided:* MVP ships the app, the website (which sitters use after joining) and two-way SMS. Sitters need SMS reminders anyway, so letting them reply by text proves the multi-channel model cheaply. WhatsApp and Discord come in V2: WhatsApp charges per conversation and requires approved templates outside a 24-hour window, and Discord already had a bot in the prototype. Slack, Telegram and replies by email come later. The model supports any channel from day one, so adding one is an adapter, not a model change.

## Runtime

**Q25. Minimum OS and browser versions.** The kernel needs only ES2017, but the apps need more: web push on iPhone needs iOS 16.4+, and current Android WebView builds need Android 10+. Every supported version also has to be in the device test matrix ([07 §7.11](07-portable-core.md#711-proving-it-the-conformance-suite)).

*Recommendation:* iOS and iPadOS 16.4+, Android 10+, and the current and previous major versions of Chrome, Edge, Firefox and Safari, plus the current Firefox ESR.

**Q26. What happens to a dose time that doesn't exist on the night clocks go forward?** At 02:30 on a spring-forward night there is no 02:30. RFC 5545 skips the occurrence; other libraries shift it forward. A skipped dose is a safety problem ([07 §7.5](07-portable-core.md#75-time)).

*Recommendation:* shift it to the first valid time after the gap and flag it to the caregiver. In the autumn overlap, use the first occurrence. Store the policy on each schedule, so it can be changed per medication.

## Home and cloud editions

From the home and cloud design ([08](08-home-and-cloud.md)).

**Q27. Should the home edition be relay-first?** With relay-first, every install gets its own HTTPS name, reached through Pawsitter's relay from any network. The alternative is LAN-first with the relay optional. That leaves sitters on guest Wi-Fi or mobile data, and owners away on the trip, with no access by default, and plain HTTP on the LAN disables passkeys, the offline copy and push.

*Recommendation:* relay-first. Accept that remote access, push, SMS and certificates need the internet, and cover outages with Q29's fallbacks rather than a plain-HTTP mode.

**Q28. Which home sign-in options, and which defaults?** The menu is in [08 §8.6](08-home-and-cloud.md#86-home-sign-in-options): paired devices, passkeys, a code to the contact the owner entered, owner approval, a personal PIN, a Pawsitter account, the console, a kiosk, trusted home Wi-Fi, and a shared household PIN.

*Recommendation:*
- Owners: passkeys with a printed recovery kit.
- Sitters: a QR join confirmed by a code, or by owner approval when there's no contact on file.
- Offline step-up: a personal PIN.
- The beta ships just that preset. The kiosk and Pawsitter-account sign-in come at GA. Leave out trusted home Wi-Fi and the shared PIN unless interviews show owners insist, and even then offer only read-only views.

**Q29. How does a home medication trip survive the house going dark?** At home, a power or internet outage would stop reminders and door-code reveals.

*Recommendation:* decide before the home beta, with three parts.
- **Backup reminders from the cloud:** a discreet 48-hour schedule that fires only if the home hasn't marked the dose done. On by default for medication trips; owners can opt out after a warning.
- **Door codes staged on the sitter's phone** for the access window, after a step-up.
- **A readiness gate** that won't call a medication trip "ready" without both.

**Q30. The home-zone domain.** Every home install's name lives under it, so passkeys and printed cards depend on it never changing.

*Recommendation:* after the product name (Q20), register a separate domain for long-term use and apply for the Public Suffix List. Run the beta on a separate, invite-only zone until the listing ships in browsers.

**Q31. What's free in the home edition?**

*Recommendation:*
- **Free:** sitter access through the relay; reminders, push and the watchdog; backup reminders; staged door codes; encrypted off-site backup of the structured data. This keeps the promise that sharing is free and safety isn't paywalled.
- **Plus:** relay bandwidth above a cap, media backup, and the hosted assistant.

**Q32. Is the native iOS owner app in the cloud MVP?** It's the only way to get Taken / Snooze / Skip on the lock screen, and time-sensitive reminders, on Apple devices. For home installs, iOS limits on per-install web addresses in an app still need testing ([08 §8.9](08-home-and-cloud.md#89-the-owner-away-from-home)).

*Recommendation:* yes, for the cloud MVP. Test per-install addresses on real devices before the home beta, with Pawsitter-account sign-in as the fallback.

## Next steps

1. Validate the offering with interviews and hands-on trials ([06 §6.8](06-feature-research.md#68-what-to-validate-next)), before locking pricing (Q19) or investing beyond MVP in "where is it?".
2. Decide Q20 (name), Q21 (owner app), Q25 (minimum versions) and Q26 (daylight-saving gaps), which shape the first build, and Q27 to Q32 before the home beta.
3. Start the long-lead items for the home edition now ([08 §8.17](08-home-and-cloud.md#817-phasing)): register the home zone, apply for the Public Suffix List, request Let's Encrypt's rate-limit exemption, and set up a backup CA.
4. Write command/query schemas (inputs, outputs, errors) for the MVP set.
5. Build the conformance corpus first ([07 §7.11](07-portable-core.md#711-proving-it-the-conformance-suite)), then the safety-critical algorithms against it: `can_administer` (including dated revisions and unverified history), recurrence across daylight-saving changes, `whats_next`, and the reminder dispatcher (repeat, escalate, supersede).
6. Specify the `ModelGateway` flow (route, reserve, settle) with concurrency tests, since overspending costs real money.
7. Plan migration of prototype data (§2.19 in the domain model).
