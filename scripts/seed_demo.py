"""Demo data for every dashboard section. Safe to rerun: existing rows are skipped.

Run after init_db.py (which creates Sonic and his real medication list):
    python3 scripts/init_db.py && python3 scripts/seed_demo.py

Schedule times below are demo times derived from the medication intervals;
the owner should replace them with the real times. Contacts are fictional
(555-01xx numbers are reserved for fiction).
"""
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import select
from src.db.manager import DatabaseManager
from src.db.models import Pet, Schedule, ActivityLog, KnowledgeItem, KnowledgeCategory, LogStatus

PETS = [
    ("Sonic", "Cat. Takes several medications (see medication list)."),
    ("Biscuit", "Golden retriever (demo pet). Friendly, loves treats, pulls on the leash."),
]

# (pet, task, time, frequency, description)
SCHEDULES = [
    ("Sonic", "Breakfast", "07:30", "daily", "1/2 can wet food in his blue bowl."),
    ("Sonic", "Methimazole", "08:00", "daily", "Orange pen, 2 clicks in ear flap (every 12 hours)."),
    ("Sonic", "Ondansetron", "07:00", "daily", "Half tablet from the flat Tupperware (every 8 hours)."),
    ("Sonic", "Ondansetron", "15:00", "daily", "Half tablet from the flat Tupperware (every 8 hours)."),
    ("Sonic", "Ondansetron", "23:00", "daily", "Half tablet from the flat Tupperware (every 8 hours)."),
    ("Sonic", "Dinner", "18:00", "daily", "1/2 can wet food in his blue bowl."),
    ("Sonic", "Methimazole", "20:00", "daily", "Orange pen, 2 clicks in ear flap (every 12 hours)."),
    ("Sonic", "Scoop litter box", "19:00", "daily", "Litter box is in the laundry room."),
    ("Biscuit", "Morning walk", "07:15", "daily", "20 minutes around the block."),
    ("Biscuit", "Breakfast", "07:45", "daily", "1 cup kibble."),
    ("Biscuit", "Evening walk", "17:30", "daily", "30 minutes, park loop."),
    ("Biscuit", "Dinner", "18:15", "daily", "1 cup kibble."),
]

# (pet or None, category, topic, content)
KNOWLEDGE = [
    (None, KnowledgeCategory.EMERGENCY, "Vet", "Happy Paws Veterinary Clinic, 555-0142. Open 8am-6pm Mon-Sat. (Demo contact)"),
    (None, KnowledgeCategory.EMERGENCY, "Emergency vet (after hours)", "City 24/7 Animal ER, 555-0199, 12 Elm Street. (Demo contact)"),
    (None, KnowledgeCategory.EMERGENCY, "Owner contact", "Text the owner at 555-0123. Call if it's urgent. (Demo contact)"),
    ("Sonic", KnowledgeCategory.INSTRUCTION, "Feeding Sonic", "1/2 can of wet food twice a day in his blue bowl. Fresh water daily. No human food."),
    ("Sonic", KnowledgeCategory.LOCATION, "Cat food", "Wet food cans are in the pantry, bottom shelf. Open cans go in the fridge with a lid."),
    ("Sonic", KnowledgeCategory.LOCATION, "Litter box", "In the laundry room. Scoop once a day; bags and scoop are on the shelf above it."),
    ("Sonic", KnowledgeCategory.LOCATION, "Cat carrier", "Grey carrier in the hall closet, in case he needs to go to the vet."),
    ("Sonic", KnowledgeCategory.GENERAL, "Sonic's personality", "Shy with new people at first. Loves chin scratches and hides under the bed when nervous."),
    ("Biscuit", KnowledgeCategory.LOCATION, "Leash and harness", "Blue nylon harness with the leash attached, in the basket near the front door."),
    ("Biscuit", KnowledgeCategory.LOCATION, "Treats", "Large airtight blue container in the pantry, second shelf from the top. Max 3 a day."),
    ("Biscuit", KnowledgeCategory.INSTRUCTION, "Feeding Biscuit", "1 cup kibble at breakfast and dinner. Kibble bin is next to the back door."),
    (None, KnowledgeCategory.GENERAL, "Wi-Fi", "Network: PawsHouse. The password is on the fridge magnet. (Demo)"),
    (None, KnowledgeCategory.GENERAL, "House rules", "Keep the back door closed so Sonic can't get out. Lock the front door when leaving."),
    # Household objects
    (None, KnowledgeCategory.LOCATION, "Spare key", "Spare house key is in the lockbox on the side gate. Code is with the owner. (Demo)"),
    (None, KnowledgeCategory.LOCATION, "First aid kit", "Pet first aid kit (gauze, saline, tweezers) is under the bathroom sink in a red bag."),
    (None, KnowledgeCategory.LOCATION, "Cleaning supplies", "Enzyme cleaner for accidents and paper towels are under the kitchen sink."),
    (None, KnowledgeCategory.LOCATION, "Trash and recycling", "Bins are in the garage. Trash day is Thursday morning; roll them to the curb Wednesday night."),
    (None, KnowledgeCategory.LOCATION, "Thermostat", "Hallway thermostat. Keep it between 68-74°F; Sonic gets cold easily."),
    (None, KnowledgeCategory.LOCATION, "Poop bags", "Roll of green poop bags is clipped to Biscuit's leash, refills in the basket by the front door."),
    (None, KnowledgeCategory.LOCATION, "Towels for pets", "Old striped towels for wiping muddy paws are on the hook by the back door."),
    ("Sonic", KnowledgeCategory.LOCATION, "Pill pockets", "Chicken pill pockets are in the fridge door. Wrap Sonic's pills in one if he refuses them."),
    ("Sonic", KnowledgeCategory.LOCATION, "Brush", "Sonic's soft brush is in the basket under the coffee table."),
    ("Biscuit", KnowledgeCategory.LOCATION, "Dog bed", "Biscuit sleeps in the big grey bed in the living room. He's allowed on the couch only with the blanket on it."),
    # Favorite things
    ("Sonic", KnowledgeCategory.GENERAL, "Sonic's favorite toys", "A feather wand (behind the bookshelf) and the crinkly yellow mouse. He loves the laser pointer, but stop after 5 minutes."),
    ("Sonic", KnowledgeCategory.GENERAL, "Sonic's favorite spots", "The sunny windowsill in the bedroom and the top of the cat tree. Hides under the bed when nervous; just leave him be."),
    ("Sonic", KnowledgeCategory.GENERAL, "Sonic's treats", "Two freeze-dried chicken treats a day max, from the small tin on the kitchen counter."),
    ("Biscuit", KnowledgeCategory.GENERAL, "Biscuit's favorite toys", "The squeaky hedgehog and a frayed rope tug toy, both in the toy bin by the couch. Tennis balls are for outside only."),
    ("Biscuit", KnowledgeCategory.GENERAL, "Biscuit's quirks", "Barks at the mail carrier around 11am, totally normal. Scared of thunder; he likes to sit in the bathtub during storms."),
    ("Biscuit", KnowledgeCategory.INSTRUCTION, "Walking Biscuit", "Use the harness, not the collar. He pulls toward squirrels, so keep a firm grip. Avoid the dog park; he's not great with big dogs."),
    # Emergencies
    ("Sonic", KnowledgeCategory.EMERGENCY, "If Sonic vomits", "One vomit is common for him; that's what the Ondansetron is for. Call the vet if he vomits more than twice in a day or stops eating."),
    (None, KnowledgeCategory.EMERGENCY, "If a pet gets out", "Shake the treat tin and call their name; don't chase. Text the owner right away. Biscuit's microchip is registered to the owner."),
]


def seed():
    db = DatabaseManager()
    db.create_db_and_tables()
    with db.get_session() as session:
        pets = {p.name: p for p in session.exec(select(Pet)).all()}
        for name, desc in PETS:
            if name not in pets:
                pet = Pet(name=name, description=desc)
                session.add(pet)
                session.commit()
                session.refresh(pet)
                pets[name] = pet
                print(f"Added pet: {name}")

        existing = {(s.pet_id, s.task_name, s.time_of_day) for s in session.exec(select(Schedule)).all()}
        for pet_name, task, time, freq, desc in SCHEDULES:
            key = (pets[pet_name].id, task, time)
            if key not in existing:
                session.add(Schedule(pet_id=key[0], task_name=task, time_of_day=time, frequency=freq, description=desc))
                print(f"Added schedule: {pet_name} {time} {task}")
        session.commit()

        topics = {k.query for k in session.exec(select(KnowledgeItem)).all()}
        for pet_name, category, topic, content in KNOWLEDGE:
            if topic not in topics:
                session.add(KnowledgeItem(
                    query=topic, content=content, category=category,
                    pet_id=pets[pet_name].id if pet_name else None,
                ))
                print(f"Added knowledge: {topic}")
        session.commit()

        # A little history from yesterday, so the Activity page isn't empty.
        if not session.exec(select(ActivityLog)).first():
            yesterday = datetime.now().astimezone() - timedelta(days=1)
            schedules = session.exec(select(Schedule)).all()
            for i, s in enumerate(schedules[:6]):
                session.add(ActivityLog(
                    pet_id=s.pet_id, schedule_id=s.id,
                    status=LogStatus.COMPLETED if i != 3 else LogStatus.MISSED,
                    timestamp=yesterday.replace(
                        hour=int(s.time_of_day[:2]), minute=int(s.time_of_day[3:]), second=0, microsecond=0
                    ).astimezone(timezone.utc),
                    notes="Took it like a champ!" if i == 1 else ("Was asleep, will try later" if i == 3 else None),
                ))
            session.commit()
            print("Added yesterday's activity log")


if __name__ == "__main__":
    seed()
