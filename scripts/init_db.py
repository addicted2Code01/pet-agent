import sys
import os

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.manager import DatabaseManager
from src.db.models import Pet

def init_db():
    print("Initializing database...")
    db = DatabaseManager()
    db.create_db_and_tables()
    print("Database and tables created successfully.")

    # Add a dummy pet for testing
    print("Adding a test pet...")
    test_pet = Pet(name="Luna", description="A very energetic calico cat.")
    db.save_item(test_pet)
    print(f"Added test pet: {test_pet.name} (ID: {test_pet.id})")

if __name__ == "__main__":
    init_db()
