import sys
import os

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.manager import DatabaseManager
from src.db.models import Pet, KnowledgeItem, KnowledgeCategory

def init_db():
    print("Initializing database...")
    db = DatabaseManager()
    db.create_db_and_tables()
    print("Database and tables created successfully.")

    # 1. Add Luna if she doesn't exist (Idempotent - Item 11)
    pets = db.get_all(Pet)
    luna = next((p for p in pets if p.name == "Luna"), None)
    
    if not luna:
        print("Adding Luna (Cat) to the database...")
        luna = Pet(name="Luna", description="A very energetic calico cat.")
        db.save_item(luna)
        print(f"Added test pet: {luna.name} (ID: {luna.id})")
    else:
        print(f"Pet '{luna.name}' already exists.")

    # 2. Seed Knowledge items based on provided medication info (Item 1 & 8)
    # This ensures the RAG is useful immediately.
    knowledge_data = [
        ("Where is the Methimazole?", "Methimazole - Orange Pen, 2 clicks spread in ear flap every 12 HOURS.", KnowledgeCategory.MEDICATION),
        ("How much Ondansetron should I give?", "Ondansetron - small white pills in bottle. HALF TABLET, every 8 HOURS. I cut these into half tablets already and left them in the flat Tupperware", KnowledgeCategory.MEDICATION),
        ("What is the Cerenia dosage?", "Cerenia - orange pill - half tablet, every 24 HOURS - try to make sure he doesn’t chew this one, it tastes very bad", KnowledgeCategory.MEDICATION),
        ("How do I give Gabapentin?", "Gabapentin - half capsule (powder) mixed into food. This will calm him down if he won’t let you give him any medications.", KnowledgeCategory.MEDICATION),
    ]

    print("Seeding knowledge base...")
    for query, content, category in knowledge_data:
        # Check if this knowledge item already exists to avoid duplicates
        existing = db.get_all(KnowledgeItem)
        if not any(k.query == query for k in existing):
            new_k = KnowledgeItem(
                query=query,
                content=content,
                category=category,
                pet_id=luna.id if luna else None
            )
            db.save_item(new_k)
            print(f"Added knowledge: {query}")
        else:
            print(f"Knowledge already exists: {query}")

if __name__ == "__main__":
    init_db()
