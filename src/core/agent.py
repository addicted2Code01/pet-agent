import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from litellm import completion
from src.core.rag_service import RAGService
from src.db.manager import DatabaseManager
from src.db.models import Pet, Schedule, ActivityLog, KnowledgeItem
from datetime import datetime

load_dotenv()

class PetAgent:
    def __init__(self, model_name: str = "openai/localhost:8000/v1"):
        # Note: litellm uses "provider/model" format. 
        # If using a local server like Ollama or LocalAI, 
        # it might be "openai/model_name" with base_url configured.
        self.model_name = model_name
        self.base_url = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
        
        self.db = DatabaseManager()
        self.rag = RAGService()
        self.rag.load_index()

    async def chat(self, user_id: str, user_input: str) -> str:
        """Handles conversational queries using RAG."""
        # 1. Get context from RAG
        context_docs = self.rag.query(user_input)
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

        # 3. Call the LLM via LiteLLM
        try:
            response = completion(
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
            return f"I'm sorry, I encountered an error while trying to help: {str(e)}"

    def log_activity(self, pet_id: int, task_name: str, status: str, notes: Optional[str] = None) -> str:
        """Logs a completed or missed activity in the database."""
        # Find the schedule item
        with self.db.get_session() as session:
            from sqlmodel import select
            statement = select(Schedule).where(Schedule.pet_id == pet_id, Schedule.task_name == task_name)
            schedule_item = session.exec(statement).first()

            new_log = ActivityLog(
                pet_id=pet_id,
                schedule_id=schedule_item.id if schedule_item else None,
                status=status,
                notes=notes
            )
            session.add(new_log)
            session.commit()
            
            if schedule_item:
                schedule_item.last_run = datetime.now()
                session.add(schedule_item)
                session.commit()
            
            return f"Successfully logged {status} for {task_name}."

    def get_pet_by_name(self, name: str) -> Optional[Pet]:
        """Finds a pet by its name."""
        with self.db.get_session() as session:
            from sqlmodel import select
            statement = select(Pet).where(Pet.name == name)
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
        agent = PetAgent(model_name="openai/test-model") # Dummy name
        print("Testing chat (this will fail if no local LLM is running)...")
        # Since we don't have a running LLM in this env, we just check if it initializes
        print("Agent initialized.")
        print(f"Pet info test: {agent.get_pet_info(1)}")

    asyncio.run(test())
