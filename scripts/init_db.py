import sys
import os

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import select
from src.db.manager import DatabaseManager
from src.db.models import Pet, KnowledgeItem, KnowledgeCategory

# Medication details exactly as provided by the owner. Do not edit doses here
# without the owner confirming them.
SONIC_KNOWLEDGE = [
    ("Methimazole", "Methimazole - Orange Pen, 2 clicks spread in ear flap every 12 HOURS."),
    ("Ondansetron", "Ondansetron - small white pills in bottle. HALF TABLET, every 8 HOURS. "
                    "The owner already cut these into half tablets and left them in the flat Tupperware."),
    ("Cerenia (only if needed)", "Cerenia - orange pill - half tablet, every 24 HOURS. Only give if needed. "
                                 "The owner gave Sonic one before leaving, so he can't have another until Tuesday morning. "
                                 "Try to make sure he doesn't chew this one, it tastes very bad."),
    ("Gabapentin", "Gabapentin - half capsule (powder) mixed into food. "
                   "This will calm him down if he won't let you give him any medications."),
]


def init_db():
    print("Initializing database...")
    db = DatabaseManager()
    db.create_db_and_tables()

    with db.get_session() as session:
        sonic = session.exec(select(Pet).where(Pet.name == "Sonic")).first()
        if not sonic:
            # Earlier test data used a placeholder pet named Luna; rename it.
            sonic = session.exec(select(Pet).where(Pet.name == "Luna")).first() or Pet(name="Sonic")
            sonic.name = "Sonic"
            sonic.description = "Cat. Takes several medications (see medication list)."
            session.add(sonic)
            session.commit()
            session.refresh(sonic)
        print(f"Pet: {sonic.name} (ID: {sonic.id})")

        existing = {k.query for k in session.exec(select(KnowledgeItem)).all()}
        for query, content in SONIC_KNOWLEDGE:
            if query in existing:
                continue
            session.add(KnowledgeItem(
                query=query,
                content=content,
                category=KnowledgeCategory.MEDICATION,
                pet_id=sonic.id,
            ))
            print(f"Added knowledge: {query}")
        session.commit()


if __name__ == "__main__":
    init_db()
