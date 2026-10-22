import os
import logging
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from litellm import acompletion
from src.core.rag_service import RAGService
from src.db.manager import DatabaseManager
from src.db.models import Pet, Schedule, ActivityLog, KnowledgeItem
from datetime import datetime, timezone
from sqlalchemy import func

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class PetAgent:
    def __init__(self, model_name: Optional[str] = None):
        # Item 4: Read model from env
        self.model_name = model_name or os.getenv("LLM_MODEL", "llama3")
        self.base_url = os.getenv("LLM_BASE_URL", "http://localhost:8080/v1")
        
        self.db = DatabaseManager()
        self.rag = RAGService()
        self.rag.load_index()

    async def chat(self, user_id: str, user_input: str) -> str:
        """Handles conversational queries using RAG."""
        try:
            # Item 5: Wrap RAG in thread to avoid blocking the event loop
            context_docs = await asyncio.to_thread(self.rag.query, user_input)
            context_text = "\n".join([doc.page_content for doc in context_docs])

            # 2. Construct the prompt
            system_prompt = f"""You are a helpful and friendly Pet Sitter AI Assistant. 
Your goal is to help the sitter with questions about the pets, their schedules, 
and where items are located in the house.

Use the following pieces of retrieved context to answer the user's question. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Keep your responses concise and helpful.

Context:
{context_text}
"""

            # 3. Call the LLM via LiteLLM (Async)
            # Item 5: Use acompletion
            response = await acompletion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                api_base=self.base_url,
                temperature=0.2
            )
            return response.choices[0].message.content

        except Exception as e:
            # Item 3: Log full error, return generic message
            logger.error(f"Error in PetAgent.chat for user {user_id}: {str(e)}", exc_info=True)
            return "I'm sorry, I encountered an error while trying to help. Please try again later."

    def log_activity(self, pet_id: int, task_name: str, status: str, notes: Optional[str] = None) -> str:
        """Logs a completed or missed activity in the database."""
        with self.db.get_session() as session:
            from sqlmodel import select
            # Item 18: Match task name more robustly if needed, but here we look for exact
            statement = select(Schedule).where(Schedule.pet_id == pet_id, Schedule.task_name == task_name)
            schedule_item = session.exec(statement).first()

            new_log = ActivityLog(
                pet_id=pet_id,
                schedule_id=schedule_item.id if schedule_item else None,
                status=status,
                notes=notes,
                timestamp=datetime.now(timezone.utc) # Item 15: Use UTC
            )
            session.add(new_log)
            session.commit()
            
            if schedule_item:
                schedule_item.last_run = datetime.now(timezone.utc)
                session.add(schedule_item)
                session.commit()
            
            return f"Successfully logged {status} for {task_name}."

    def get_pet_by_name(self, name: str) -> Optional[Pet]:
        """Finds a pet by its name (case-insensitive)."""
        # Item 17: Case-insensitive lookup
        with self.db.get_session() as session:
            from sqlmodel import select
            statement = select(Pet).where(func.lower(Pet.name) == name.lower())
            return session.exec(statement).first()

    def get_pet_info(self, pet_id: int) -> str:
        """Returns basic info about a pet."""
        with self.db.get_session() as session:
            pet = session.get(Pet, pet_id)
            if not pet:
                return "Pet not found."
            return f"Pet: {pet.name}\nDescription: {pet.description}"

if __name__ == "__main__":
    # Quick test (Requires a running local LLM server)
    import asyncio
    
    async def test():
        agent = PetAgent()
        print("Testing agent initialization...")
        print(f"Model: {agent.model_name}")
        print(f"Base URL: {agent.base_url}")
        print("Agent initialized.")
        # Test pet info (assuming Luna is in DB)
        # We can't easily run async in a simple script without knowing if DB is ready
        # but we'll assume init_db.py was run.
        try:
            print(f"Pet info test (Luna): {agent.get_pet_info(1)}")
        except Exception as e:
            print(f"Pet info test failed (this is okay if DB not seeded): {e}")

    asyncio.run(test())
