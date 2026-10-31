# 5. Open questions

Decisions needed before building, roughly in order of how much they shape the core. Each has a recommendation; mark it ✅ when decided.

## Product & market

**Q1. Who is the first paying customer?**
- (a) Pet owners (households) who share access with sitters, friends and family.
- (b) Professional sitters/walkers managing many client households.
- (c) Clinics and boarding facilities.

*Recommendation:* (a) first. The model already supports many accounts per user, so (b) can follow as a tier without a rewrite. (c) needs cross-account sharing, so later.

**Q2. Cloud, local-first, or hybrid?** (See [03 §3.9](03-core-architecture.md#39-deployment-shapes).)
The prototype's pitch was "nothing leaves your home". A product sitters use from their own phones, away from your Wi-Fi, mostly wants the cloud.

*Recommendation:* cloud first, with strong privacy (encrypted secrets, EXIF stripping, egress policies). Keep the core storage-agnostic so a self-hosted edition is possible. Defer hybrid sync.

**Q3. Does the AI assistant run locally or hosted?** It affects cost, quality and what data it may see.

*Recommendation:* make it pluggable via the `LanguageModel` port and egress policy. Default to a hosted model on `normal` data in the cloud product; a local model in self-hosted.

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

## Next steps once these are answered

1. Lock the MVP feature list (01) against the answers.
2. Write command/query schemas (inputs, outputs, errors) for the MVP set.
3. Write a test-first spec for `can_administer`, recurrence/DST and `whats_next`, the three safety-critical algorithms.
4. Plan migration of prototype data (§2.15 in the domain model).
