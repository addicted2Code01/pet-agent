# 6. Feature research: what customers value

Researched 2026-11-03 across app-store listings, vendor sites, review sites (Capterra, G2), sitter trade articles and veterinary sources. **Evidence quality:** most of it is listing copy and review-site summaries, not hands-on testing or surveys. Reddit and Indie Hackers couldn't be reached from the research environment. Treat scores as informed judgment, and validate the top bets with interviews (§6.8).

## 6.1 Summary

1. **The features customers value most are the basic ones:** reminders that actually fire, a shared log of who did what, and photo updates while they're away. Complaints cluster where apps get these wrong, such as reminders that don't fire or data lost in sync.
2. **Setup effort decides whether anyone gets value.** Ease of use is what inventory-app users praise most, and comparisons steer people away from dense ones. Every structured feature in our spec depends on owners entering data, so fast setup ranks in the top tier.
3. **Our differentiators are open ground.** No competitor found offers computed dose safety ("can I give it now?"), a "where is it?" for items and supplies, or expiring sitter access with logged code reveals. The evidence for dose safety is strong but indirect (medication errors and owner anxiety). "Where is it?" is our least-evidenced bet.
4. **The spec needs a few changes:** move medication reminders and push notifications to MVP; add seven features, most of them small (vet authorization, missed-dose instructions, care-note import, print view, offline copy, "I'm home", discreet notifications); and don't build in-app chat or vet telehealth (§6.6).
5. **Business lessons:** keep sharing with a sitter free and friction-free, never take features away from existing users, and make reliability the brand.

## 6.2 How features were scored

| Dimension | Weight | 5 means | 1 means |
|---|---|---|---|
| **Demand** | 40 % | Nearly every relevant competitor leads with it, or customers praise or request it often | Barely mentioned |
| **Impact** | 40 % | When it's missing or fails, it's a top complaint or a safety risk | Nice to have |
| **Fit** | 20 % | Central to our first customer: households sharing care with sitters | Mostly for other segments |

**Score** = 20 × (0.4 × Demand + 0.4 × Impact + 0.2 × Fit), out of 100. **Cost** (S, M, L, relative to the core in [03](03-core-architecture.md)) isn't in the score but shapes the recommendation.

**Tiers:** 84 and up = must have at launch · 68–80 = strong, launch if possible · 56–64 = cheap wins or later · below 50 = don't build.

## 6.3 Ranked features

D·I·F = Demand · Impact · Fit.

### Tier 1: must have at launch

| # | Feature | D·I·F | Score | Cost | Spec today | Recommendation |
|---|---|---|---|---|---|---|
| 1 | Medication reminders that reliably fire: persistent until answered, one-tap Taken / Snooze / Skip | 5·5·5 | 100 | M | V2 (01 §1.6) | **Move to MVP** |
| 2 | Shared log of who did what and when (doses, meals, walks); reminders clear for everyone once someone logs it | 5·5·5 | 100 | S | MVP | Keep; add clearing everyone's reminder |
| 3 | Photo updates and visit reports, pushed in real time | 5·5·4 | 96 | M | MVP report; push is V2 | **Push notifications in MVP** |
| 4 | Care guide by link: the sitter needs no app or account | 5·4·5 | 92 | M | Open (Q11) | **Settle Q11: yes, MVP** |
| 5 | Complete care sheet and emergency card: health baseline, when to call the vet, tap-to-call contacts | 4·5·5 | 92 | S | MVP | Keep |
| 6 | Fast setup: starter templates, and import of an existing care note that AI turns into draft entries for the owner to confirm | 4·5·5 | 92 | M | Missing | **Add to MVP** |
| 7 | Dose safety: "can I give it now?" from minimum gap, daily maximum and "not before" | 3·5·5 | 84 | M | MVP | Keep; lead the pitch with it |
| 8 | Missed or refused doses: per-medication "if missed / if refused" instructions, and an instant alert to the owner | 3·5·5 | 84 | S | Partly (statuses exist) | **Add fields and alert** |
| 9 | Today checklist: what's next, what's overdue | 4·4·5 | 84 | S | MVP | Keep |

### Tier 2: strong, launch if possible

| # | Feature | D·I·F | Score | Cost | Spec today | Recommendation |
|---|---|---|---|---|---|---|
| 10 | Vet treatment authorization with a spending limit, per sitter | 3·5·4 | 80 | S | Missing | **Add to MVP** |
| 11 | Flexible doses and schedules: ½ tablet, ml by syringe, clicks, every N hours, tapering | 3·4·5 | 76 | S | MVP (tapering via revisions) | Keep; test fractional doses in the UI |
| 12 | Sitter access that expires and can be revoked, limited to chosen pets and places | 3·4·5 | 76 | M | MVP | Keep |
| 13 | Door, alarm and lockbox codes for the sitter, with a photo of where the lockbox is and a reveal history | 3·4·5 | 76 | M | MVP | Keep |
| 14 | Incident reports that alert the owner | 3·4·5 | 76 | S | MVP | Keep |
| 15 | "Where is it?" for items and supplies, with photos of the spot | 2·4·5 | 68 | M | MVP | Keep, but validate first (§6.8) |
| 16 | Health records: vaccinations, weight, vet visits | 4·3·3 | 68 | M | V2 | Keep V2; allow a vaccination certificate upload in MVP |
| 17 | Proof of visit: check-in/out times, optional GPS | 4·3·3 | 68 | M | V2 | Keep V2 and opt-in; MVP proof = timestamps and photos |

### Tier 3: cheap wins or later

| # | Feature | D·I·F | Score | Cost | Spec today | Recommendation |
|---|---|---|---|---|---|---|
| 18 | Supplies running low → shopping list; refill reminders | 3·3·4 | 64 | M | MVP stock, V2 refills | **Simplify:** plenty / low / out, exact counts optional |
| 19 | Offline copy of the care sheet and emergency card | 2·4·4 | 64 | S | V2 (full offline) | **Read-only offline copy in MVP** |
| 20 | Printable care sheet and emergency card | 3·3·4 | 64 | S | V2 (export) | **Print view in MVP**; PDF/CSV export stays V2 |
| 21 | AI assistant answering from the household's own data | 3·3·4 | 64 | L | MVP | Keep, narrowly: grounded answers for sitters, no diagnosis |
| 22 | Owner–sitter chat inside the app | 4·3·2 | 64 | L | Not planned | **Don't build**; comments on tasks and incidents, plus tap-to-text |
| 23 | "I'm home" handback: closes access, sends the stay summary | 2·3·5 | 60 | S | Partly (access lag) | **Add to MVP** |
| 24 | Discreet notifications: hide medication names on the lock screen | 2·3·4 | 56 | S | Missing | **Add to MVP** |

### Don't build

| # | Feature | D·I·F | Score | Why not |
|---|---|---|---|---|
| 25 | Vet chat / telehealth | 3·2·1 | 44 | Funded incumbents (Petcube, Airvet) and regulatory weight; link to the pet's own vet and emergency vet instead. |
| 26 | Physical key tracking (who holds which key) | 2·2·2 | 40 | A pro-sitter need; a key can be modeled as a tracked item later if asked. |

## 6.4 Evidence by feature

1. **Reliable reminders.** Muzzly's headline features are reminders that persist until answered, with one-tap Taken/Snooze/Skip ([Muzzly, App Store](https://apps.apple.com/pl/app/muzzly-pet-meds-reminders/id6761260557)). The lowest-rated reminder apps draw "reminders don't work" ([Pet Medication Reminder, Google Play](https://play.google.com/store/apps/details?id=androidapps.angel.petmedicationreminder&hl=en_US)) and "my phone's alarm does this for free", plus requests for audible alerts ([TailCare](https://apps.apple.com/us/app/pet-medicine-reminder-tailcare/id6741084481)).
2. **Shared log.** Shared medication apps sell the same promise: once one person logs a dose, everyone else's reminder goes quiet ([PetPill](https://apps.apple.com/app/id6760020801), [Muzzly, Google Play](https://play.google.com/store/apps/details?id=io.muzzly.app)), and you can see who gave each dose ([PokiPaw](https://carnetanimale.pages.dev/blog/how-pokipaw-medication-tracker-works)). A whole category of apps exists only to answer "who fed the dog?" ([Hound](https://apps.appfollow.io/ios/hound-family-pet-care/1564604025?country=us), [Paw Clock](https://apps.apple.com/us/app/pawclock/id6761330503), [Pet Feeder App](https://apps.apple.com/app/id6758022385)).
3. **Photo updates, pushed.** Report cards with photos are Time To Pet's most praised feature ([G2](https://www.g2.com/products/time-to-pet/reviews), [Capterra](https://www.capterra.com/p/144329/Time-To-Pet/reviews/)). One Capterra reviewer warns that email-only updates get missed when clients opt out of email. Rover sends photo and video updates and a walk report with map, pee/poo and food/water ([Rover, App Store](https://apps.apple.com/gb/app/rover-com/id547320928)). Rover's own survey says 83 % of US dog owners have worried their walker "cut corners" ([Rover Cards release](https://laopinion.com/latinowire/rover-com-releases-rover-cards-new-dog-walking-technology-that-offers-peace-of-mind-to-u-s-pet-owners); company-sponsored). Industry guides call real-time photo updates a baseline expectation and communication a top owner concern ([Dojo Business](https://dojobusiness.com/blogs/news/pet-sitter-customer-segments), [Scout](https://www.scoutforpets.com/post/understanding-the-psychology-of-pet-owners-tips-for-pet-sitters)).
4. **Link access, no app.** Every care-guide app leads with sharing by one link ([Pawzfolio](https://www.producthunt.com/products/pawzfolio/makers), [Meet My Pet](https://www.producthunt.com/posts/meet-my-pet-app), [Wagabond Pets](https://appfelstrudel.com/id/6756238868/wagabond-pets.html)). Pawzfolio stresses "no app download, no account needed" ([founder's post](https://www.indiehackers.com/post/hey-ih-im-building-pawzfolio-and-wanted-to-share-where-things-stand-what-i-ve-learned-and-where-i-m-stuck-vn4T0h9kYTFEHBXJL5TA), via search summary).
5. **Care sheet and emergency card.** Sitters advise owners to "put it all in writing" and say most bad situations come from unclear expectations. They also need each pet's normal quirks to judge "watch and wait" versus "call the vet now" ([SheKnows](https://www.sheknows.com/living/articles/1097333/dog-sitter-wishes-you-knew/), [Pawrade](https://www.pawrade.com/resource/grooming/4-things-your-dog-sitter-wishes-you-knew), [AOL](https://www.aol.com/articles/things-pet-sitter-probably-doesn-185332160.html)). Standard sitter forms include medications, conditions and emergency contacts ([signNow guide](https://www.signnow.com/info-forms/62319-what-is-a-pet-sitting-form-essential-guide-for-pet-owners)). Pawzfolio advertises tap-to-call the vet.
6. **Fast setup.** Ease of use is Sortly's most common praise (rated 4.6/5), while one reviewer says it takes time to learn and set up ([Capterra](https://www.capterra.com/p/169199/Sortly-Pro/reviews/)). Grocy's interface is described as dense, with 12 top-level menu items, and comparisons recommend the simpler Homebox for inventory alone ([Grocy vs Homebox](https://selfhosting.sh/compare/grocy-vs-homebox/)). The prototype already turns free-text notes into knowledge, so drafting structured entries from an owner's existing care note is a natural AI job, as long as the owner confirms each entry.
7. **Dose safety.** None of the medication apps found advertises lockouts; they remind and log. A boarding-industry guide treats a missed, wrong, late or double dose as a potential emergency, and a negligence risk when instructions are vague ([boarding guide](https://www.pawsdogdaycare.com/Start-Up-Services/Medication-Error-Boarding-Medical-Instructions.htm)). The FDA and medication-safety groups warn about pet medication errors and recommend written instructions for sitters ([FDA](https://www.fda.gov/consumers/consumer-updates/medication-errors-happen-pets-too), [Consumer Med Safety](https://www.consumermedsafety.org/safety-articles/top-10-tips-to-keep-pets-safe-around-medicines)). A 2025 analysis of about 4,800 owner posts found significant anxiety around giving dogs oral medication ([Frontiers in Veterinary Science](https://www.frontiersin.org/journals/veterinary-science/articles/10.3389/fvets.2025.1502236/pdf)). In a 2016 survey, about 90 % of professional sitters said they care for or medicate special-needs pets, mostly at no extra charge ([PSI](https://petsit.com/psi-releases-2016-pet-sitting-state-of-the-industry-results)).
8. **Missed or refused doses.** In one Rover case, a sitter quietly stopped a cat's medication for two days because the cat disliked it, and the owner found out only when symptoms returned ([Rover Community](https://www.rover.com/community/question/31059/my-cat-was-prescribed-an-otc-medication-the-sitter-stopped-giving-it-to-her-two-days-ago-without-consulting-me-what-would-you-do)). Vet guidance: don't double up after a missed dose ([Vetstreet](https://vetstreet.com/?p=2299)), and call the vet if more than one is missed or the drug treats seizures, heart disease or diabetes ([Vetscriptions](https://www.vetscriptions.co.uk/blogs/pet-medications/what-happens-if-you-miss-a-dose-of-pet-medication)).
9. **Today checklist.** The "who fed the dog" apps (feature 2) sell more than feeding logs: Hound advertises checking "if someone already took it out", and Pet Feeder App promises "no double-feeding or missed meals".
10. **Vet authorization.** Vet release forms with a pre-approved spending limit are standard in sitter paperwork. They say when the sitter may act, the most they may spend without asking, and exclusions such as euthanasia ([Jotform vet release](https://form.jotform.com/243037284221045), [LegalZoom agreement](https://42.legalzoom.com/templates/t/pet-sitting-agreement), [signNow guide](https://www.signnow.com/info-forms/62319-what-is-a-pet-sitting-form-essential-guide-for-pet-owners)).
11. **Flexible doses.** The one written complaint about Pet Pill Reminder & Tracker is the lack of half-tablet and syringe options ([App Store](https://apps.apple.com/us/app/pet-pill-reminder-tracker/id6755349743)). Vets warn that a misread "5.0 mg" can become a tenfold overdose ([dvm360](https://www.dvm360.com/view/pharmacy-relations-101-common-sources-of-error-and-prevention-strategies)).
12. **Expiring access.** Wagabond's links expire on a schedule and can be revoked. Security vendors recommend sitter-specific codes that only work during scheduled windows ([Guardian Alarm](https://guardianalarm.com/blog/blog-pet-sitter-smart-lock-security-guide/)).
13. **Codes and lockbox photos.** Pro software stores lockbox codes per client, generates random key codes and tracks keys ([Time To Pet](https://www.timetopet.com/blog/key-management-for-pet-sitters-and-dog-walkers), [random codes](https://www.timetopet.com/blog/friday-feature-focus-random-key-codes)). Pet Sitter Plus restricts who can see each code field and suggests photos of hidden lockboxes and alarm keypads ([Pet Sitter Plus](https://petsitterplus.freshdesk.com/support/solutions/articles/101000428609-add-access-to-property-details)). Guardian Alarm logs when a sitter came and went.
14. **Incidents.** Same sources as features 5 and 7: sitters need a clear threshold for escalating, and owners need to hear about problems immediately.
15. **"Where is it?"** Direct evidence is thin: no review asks for it, and no pet app offers it. The indirect evidence is lockbox photos in pro software (feature 13) and the photos customers praise in Sortly. This is a bet; interviews should test it before we invest heavily.
16. **Health records.** 11pets users praise weight and medication tracking, but one aggregator puts its rating around 2.1, with complaints about data loss, sync bugs and a switch to subscriptions ([review analysis](https://kimola.com/reports/in-depth-analysis-of-11pets-pet-care-user-feedback-app-store-us-150767), [AppFollow](https://appfollow.io/ios/11pets-pet-care/1232470530?country=us)). Petcube pitches "one record per pet" ([Petcube](https://petcube.com/news/petcube-launches-all-in-one-intelligent-pet-care-app-2/)), and Wagabond includes vaccination status in its sitter link.
17. **Proof of visit.** Time To Pet can show clients GPS and time data ([help article](https://help.timetopet.com/article/23-viewing-time-tracking-and-gps-data)). Rover warns that background GPS drains the battery. For friends and family sitting, GPS tracking is sensitive (Q12).
18. **Supplies.** Grocy's best-loved trick adds an item to the shopping list automatically when it drops below a minimum ([Grocy vs Homebox](https://selfhosting.sh/compare/grocy-vs-homebox/)). Sortly has low-stock reports ([Sortly](https://www.sortly.com/home-inventory)), and Muzzly has refill reminders. Our judgment: precise counting is the heavy part for households, so a plenty / low / out status keeps the shopping list without the counting.
19. **Offline.** Muzzly advertises working fully offline. Sitters lose signal in basements and garages (Q14).
20. **Print.** Sortly reviewers "love" PDF export. Printable pet-sitter planners sell on Etsy ([example](https://www.etsy.com/listing/4487742972)).
21. **AI assistant.** Petcube charges $9.99/month for its AI assistant plus vet chat. An independent test of seven AI pet-health apps warns of "dangerous false confidence" ([test](https://blogstarterhub.pages.dev/pets/ai-pet-health-apps-detect-illness-early-2026)). AI vet apps draw billing and cancellation complaints ([AskVet summary](https://marlvel.ai/intel-report/lifestyle/askvet-online-pet-care)). So our AI should answer from the household's data and help with setup, not diagnose.
22. **Chat.** Messaging is central to Rover and Time To Pet ([Time To Pet conversations](https://www.timetopet.com/client-management/conversations)), but households already text their sitters. Building chat is costly and adds little for them.
23. **Handback.** Sitter advice articles say most sitters require clients to call or text when they get home ([SheKnows](https://www.sheknows.com/living/articles/1097333/dog-sitter-wishes-you-knew/), [Petful](https://www.petful.com/misc/pet-sitter-pet-peeves/)). An "I'm home" button replaces that text, closes access and sends the stay summary.
24. **Discreet notifications.** Muzzly offers a discreet mode that hides medication names.

## 6.5 Complaints and pitfalls

| Problem | Seen in | What we do instead |
|---|---|---|
| Reminders that don't fire | Low-rated reminder apps | Notification delivery is a tested, monitored feature (feature 1) |
| Data loss and sync bugs | 11pets (rating about 2.1) | Server-side source of truth, idempotent writes, backups ([03](03-core-architecture.md)) |
| Subscriptions introduced on existing users; punitive pricing for home users | 11pets, Sortly | Never remove features from existing users; price for households |
| Sharing behind a paywall (a pitfall rather than a documented complaint: sharing is our core loop) | Pawzfolio ($4.99/month to share), Muzzly, PetPill | Sharing with a sitter is free |
| Hard cancellation, surprise billing | AI vet apps | One-tap cancellation; no overage without opt-in (Q18) |
| Dense, complicated screens | Grocy | Three-level places in the UI (Q5); optional counts (feature 18) |
| Updates sent only by email | Time To Pet review | Push first, email as backup |
| Battery drain from background GPS | Rover | No continuous tracking; GPS only at check-in, opt-in |
| AI with false confidence on health | AI pet-health apps | Computed answers, verbatim instructions, no diagnosis (principle 2) |

## 6.6 Recommended changes to the spec

All of these were applied in draft 0.3. The "Spec today" column in §6.3 shows the spec as it was before that. Draft 0.4 then added a care thread at the owner's request ([01 §1.14](01-features.md#114-care-thread--ai-oversight)): narrower than the general chat ruled out in #22, it exists so the owner can see and correct the AI's answers to sitters.

| Change | Where | Features |
|---|---|---|
| Medication reminders and overdue alerts move to MVP (settles Q15) | 01 §1.6, 05 Q15 | 1 |
| Push notifications in MVP for reminders, refused or missed doses, urgent incidents and visit reports | 01 §1.8 | 1, 3, 8 |
| Logging a dose or task clears the reminder for every caregiver | 03 §3.6 (sweeper), 01 §1.6 | 2 |
| Link-only sitter access in MVP (settles Q11) | 01 §1.1, 05 Q11 | 4 |
| Starter templates and care-note import: AI drafts entries, the owner confirms each | 01 new row, 03 §3.10 (metered) | 6 |
| `if_missed` and `if_refused` instructions on medication orders; alert the owner on refused, skipped or missed doses | 02 §2.8, 01 §1.5 | 8 |
| Vet treatment authorization with spending limit and exclusions, per engagement, shown on the emergency card | 02 §2.4 (Engagement), 01 §1.7 | 10 |
| Supplies: quick status (plenty / low / out) with exact counts optional | 02 §2.7, 01 §1.4 | 18 |
| Read-only offline copy of the care sheet and emergency card (partly settles Q14) | 01 §1.9, 05 Q14 | 19 |
| Print view of the care sheet and emergency card | 01 §1.8 | 20 |
| AI assistant scoped to grounded answers for sitters and setup help; no diagnosis | 01 §1.9 | 21 |
| "I'm home" handback | 01 §1.1 | 23 |
| Discreet notifications | 01 §1.8 | 24 |
| Vaccination certificate upload on the pet in MVP; structured health records stay V2 | 01 §1.3 | 16 |
| Don't build: in-app chat, vet telehealth, AI diagnosis | 01 §1.9 | 22, 25 |

## 6.7 Pricing signals

Useful for Q17–Q19.

| App | What's paid | Price |
|---|---|---|
| Pawzfolio | Sharing the care guide | $4.99/month (early-stage figure; may have changed) |
| Muzzly | Sharing with family and sitters (Premium) | Not published in listing |
| PetPill | Family sharing (Pro) | Not published in listing |
| PokiPaw | Sharing free for 2 members | Free tier |
| PetPillBox | Everything | €9.99 one-time |
| Petcube | AI assistant and 24/7 vet chat | $9.99/month or $99.99/year |
| PawSitter (sitter business app) | Premium | $7.99/month or $59.99/year |

## 6.8 What to validate next

1. **Interviews:** 5–10 owners who use sitters and 5 sitters (friends and professionals). Test whether "where is it?" and dose safety solve problems they recognize, how they share instructions today, and what they'd pay.
2. **Hands-on trials:** Muzzly, Hound, Pawzfolio or Wagabond, and the Petcube app. Confirm the gaps in §6.4 are real and note anything they do well.
3. **Setup-time target:** measure how long it takes a new owner to produce a care guide a sitter can use. Aim for under 10 minutes with templates and import.

## Sources

Medication and family apps: [Muzzly (App Store)](https://apps.apple.com/pl/app/muzzly-pet-meds-reminders/id6761260557) · [Muzzly (Google Play)](https://play.google.com/store/apps/details?id=io.muzzly.app) · [PetPill](https://apps.apple.com/app/id6760020801) · [PokiPaw](https://carnetanimale.pages.dev/blog/how-pokipaw-medication-tracker-works) · [Pet Pill Reminder & Tracker](https://apps.apple.com/us/app/pet-pill-reminder-tracker/id6755349743) · [TailCare](https://apps.apple.com/us/app/pet-medicine-reminder-tailcare/id6741084481) · [Pet Medication Reminder](https://play.google.com/store/apps/details?id=androidapps.angel.petmedicationreminder&hl=en_US) · [Hound](https://apps.appfollow.io/ios/hound-family-pet-care/1564604025?country=us) · [Paw Clock](https://apps.apple.com/us/app/pawclock/id6761330503) · [Pet Feeder App](https://apps.apple.com/app/id6758022385) · [11pets review analysis](https://kimola.com/reports/in-depth-analysis-of-11pets-pet-care-user-feedback-app-store-us-150767) · [11pets on AppFollow](https://appfollow.io/ios/11pets-pet-care/1232470530?country=us)

Care guides and sitters: [Pawzfolio](https://www.producthunt.com/products/pawzfolio/makers) · [Pawzfolio founder post](https://www.indiehackers.com/post/hey-ih-im-building-pawzfolio-and-wanted-to-share-where-things-stand-what-i-ve-learned-and-where-i-m-stuck-vn4T0h9kYTFEHBXJL5TA) · [Meet My Pet](https://www.producthunt.com/posts/meet-my-pet-app) · [Wagabond Pets](https://appfelstrudel.com/id/6756238868/wagabond-pets.html) · [Rover (App Store)](https://apps.apple.com/gb/app/rover-com/id547320928) · [Rover Cards release](https://laopinion.com/latinowire/rover-com-releases-rover-cards-new-dog-walking-technology-that-offers-peace-of-mind-to-u-s-pet-owners) · [Rover Community case](https://www.rover.com/community/question/31059/my-cat-was-prescribed-an-otc-medication-the-sitter-stopped-giving-it-to-her-two-days-ago-without-consulting-me-what-would-you-do) · [Time To Pet on G2](https://www.g2.com/products/time-to-pet/reviews) · [Time To Pet on Capterra](https://www.capterra.com/p/144329/Time-To-Pet/reviews/) · [Time To Pet GPS](https://help.timetopet.com/article/23-viewing-time-tracking-and-gps-data) · [Time To Pet conversations](https://www.timetopet.com/client-management/conversations) · [Time To Pet key management](https://www.timetopet.com/blog/key-management-for-pet-sitters-and-dog-walkers) · [Time To Pet random key codes](https://www.timetopet.com/blog/friday-feature-focus-random-key-codes) · [Pet Sitter Plus property access](https://petsitterplus.freshdesk.com/support/solutions/articles/101000428609-add-access-to-property-details) · [Guardian Alarm](https://guardianalarm.com/blog/blog-pet-sitter-smart-lock-security-guide/) · [SheKnows](https://www.sheknows.com/living/articles/1097333/dog-sitter-wishes-you-knew/) · [Pawrade](https://www.pawrade.com/resource/grooming/4-things-your-dog-sitter-wishes-you-knew) · [AOL](https://www.aol.com/articles/things-pet-sitter-probably-doesn-185332160.html) · [Petful](https://www.petful.com/misc/pet-sitter-pet-peeves/) · [Dojo Business](https://dojobusiness.com/blogs/news/pet-sitter-customer-segments) · [Scout](https://www.scoutforpets.com/post/understanding-the-psychology-of-pet-owners-tips-for-pet-sitters) · [PSI 2016 survey](https://petsit.com/psi-releases-2016-pet-sitting-state-of-the-industry-results) · [Jotform vet release](https://form.jotform.com/243037284221045) · [LegalZoom agreement](https://42.legalzoom.com/templates/t/pet-sitting-agreement) · [signNow guide](https://www.signnow.com/info-forms/62319-what-is-a-pet-sitting-form-essential-guide-for-pet-owners) · [Etsy planner](https://www.etsy.com/listing/4487742972)

Medication safety: [Boarding guide](https://www.pawsdogdaycare.com/Start-Up-Services/Medication-Error-Boarding-Medical-Instructions.htm) · [FDA](https://www.fda.gov/consumers/consumer-updates/medication-errors-happen-pets-too) · [Consumer Med Safety](https://www.consumermedsafety.org/safety-articles/top-10-tips-to-keep-pets-safe-around-medicines) · [Frontiers 2025 study](https://www.frontiersin.org/journals/veterinary-science/articles/10.3389/fvets.2025.1502236/pdf) · [Vetstreet](https://vetstreet.com/?p=2299) · [Vetscriptions](https://www.vetscriptions.co.uk/blogs/pet-medications/what-happens-if-you-miss-a-dose-of-pet-medication) · [dvm360](https://www.dvm360.com/view/pharmacy-relations-101-common-sources-of-error-and-prevention-strategies)

AI and inventory: [Petcube launch](https://petcube.com/news/petcube-launches-all-in-one-intelligent-pet-care-app-2/) · [AI pet-health app test](https://blogstarterhub.pages.dev/pets/ai-pet-health-apps-detect-illness-early-2026) · [AskVet summary](https://marlvel.ai/intel-report/lifestyle/askvet-online-pet-care) · [Sortly on Capterra](https://www.capterra.com/p/169199/Sortly-Pro/reviews/) · [Sortly home inventory](https://www.sortly.com/home-inventory) · [Grocy vs Homebox](https://selfhosting.sh/compare/grocy-vs-homebox/)
