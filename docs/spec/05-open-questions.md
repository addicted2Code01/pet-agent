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

**Q11. Do caregivers need an account to help?** A "magic link" guest view would lower friction for a neighbor watching the cat once.

*Recommendation:* allow link-only guest access, scoped to one engagement, with no secrets.

**Q12. Can the owner see a caregiver's location** (check-in geofence)? It's useful for pros and sensitive for friends.

*Recommendation:* opt-in per engagement, V2.

## Technical

**Q13. Core language.** Python (continuity with the prototype, AI ecosystem) or TypeScript (one language with web/mobile)?

**Q14. Offline support in MVP?** Sitters in basements and garages lose signal. Offline completion of tasks and doses is valuable, but sync adds complexity.

*Recommendation:* design for it now (ids, versions, idempotent commands). Ship online-only MVP with a queued-retry client, and full offline in V2.

**Q15. Notifications in MVP?** Reminders and overdue alerts are core value for medications.

*Recommendation:* MVP with push + email for overdue medications and urgent incidents only.

## Placement & AI usage

**Q16. Edge node in MVP or V2?**

*Recommendation:* V2. The MVP builds the seams it needs ([03 §3.9.5](03-core-architecture.md#395-rules-the-core-follows-from-day-one)), so adding it later is one adapter plus configuration. Pull it into MVP only if a local model is a launch requirement.

**Q17. What unit do customers see their allotment in:** credits, tokens or money?

*Recommendation:* show a simple meter ("62 % of this month's AI used, resets Nov 15"), backed by credits whose rates track provider cost. A pricier model then uses the allotment faster, and margins hold when provider prices change. Rolling token and request limits are there only to stop abuse.

**Q18. What happens when the allotment runs out?**

*Recommendation:* in MVP, hosted AI stops until the period resets and every care feature keeps working. In V2, fall back to the owner's edge node or a cheaper model, and sell top-ups. Never bill overage without an opt-in.

**Q19. How big is each plan's allotment?**

*Recommendation:* measure first. Run the beta with generous limits, record the cost per active household for four weeks, then set the standard allotment near the 90th percentile of monthly use.

## Next steps once these are answered

1. Lock the MVP feature list (01) against the answers.
2. Write command/query schemas (inputs, outputs, errors) for the MVP set.
3. Write a test-first spec for `can_administer`, recurrence/DST and `whats_next`, the three safety-critical algorithms.
4. Specify the `ModelGateway` flow (route, reserve, settle) with concurrency tests, since overspending costs real money.
5. Plan migration of prototype data (§2.16 in the domain model).
