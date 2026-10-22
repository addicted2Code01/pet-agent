import os
import logging
from typing import Optional, List, Dict
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import func
from sqlmodel import select

from src.db.manager import DatabaseManager
from src.db.models import Pet, Schedule, ActivityLog, KnowledgeItem, KnowledgeCategory, to_local

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Emergency information first, so the model sees it before anything else.
CATEGORY_ORDER = [
    KnowledgeCategory.EMERGENCY,
    KnowledgeCategory.MEDICATION,
    KnowledgeCategory.INSTRUCTION,
    KnowledgeCategory.LOCATION,
    KnowledgeCategory.GENERAL,
]

SYSTEM_RULES = """You are a Pet Sitter Assistant. You help a pet sitter care for the owner's pets.

Rules:
- Answer ONLY from the household information below. Never guess or invent details.
- For medication, state the drug, dose, timing and location exactly as written.
- If the answer is not in the information, say you don't know and tell the sitter to contact the owner.
- If something sounds like an emergency, give any emergency contacts and vet information first.
- For "what's next" or timing questions, use "Right now" and the schedule statuses below:
  OVERDUE tasks first, then the "Next up" task. Don't do your own time arithmetic.
- Keep answers short and clear."""


def ago(delta) -> str:
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return f"{minutes} min ago"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m ago" if hours < 24 else f"{hours // 24} day(s) ago"


class PetAgent:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("LLM_MODEL", "local-model")
        self.base_url = os.getenv("LLM_BASE_URL", "http://localhost:8080/v1")
        self.client = OpenAI(base_url=self.base_url, api_key=os.getenv("LLM_API_KEY", "not-needed"), timeout=300)
        self.db = DatabaseManager()

    def build_context(self, now: Optional[datetime] = None) -> str:
        """All household knowledge, plus the current time and today's task status."""
        now = now or datetime.now().astimezone()
        with self.db.get_session() as session:
            pets = session.exec(select(Pet)).all()
            pet_names = {p.id: p.name for p in pets}
            items = session.exec(select(KnowledgeItem)).all()
            schedules = session.exec(select(Schedule)).all()
            logs = sorted(session.exec(select(ActivityLog)).all(), key=lambda l: l.timestamp, reverse=True)
            schedule_names = {s.id: s.task_name for s in schedules}

        done_at = {}
        for log in logs:
            when = to_local(log.timestamp)
            if log.schedule_id and when.date() == now.date() and log.schedule_id not in done_at:
                done_at[log.schedule_id] = when

        lines = [f"## Right now\n{now.strftime('%A, %B %d, %Y, %I:%M %p').replace(' 0', ' ')}\n", "## Pets"]
        lines += [f"- {p.name}: {p.description or ''}" for p in pets] or ["- (none)"]

        for category in CATEGORY_ORDER:
            group = [i for i in items if i.category == category]
            if not group:
                continue
            lines.append(f"\n## {category.value.title()}")
            for i in group:
                pet = f" [{pet_names.get(i.pet_id)}]" if i.pet_id in pet_names else ""
                lines.append(f"- {i.query}{pet}: {i.content}")

        if schedules:
            lines.append("\n## Today's schedule")
            current = now.strftime("%H:%M")
            next_up = None
            for s in sorted(schedules, key=lambda s: s.time_of_day):
                if s.id in done_at:
                    state = f"done at {done_at[s.id].strftime('%H:%M')}"
                elif s.time_of_day < current:
                    state = "OVERDUE"
                else:
                    state = "upcoming"
                    next_up = next_up or s
                lines.append(f"- {s.time_of_day} {pet_names.get(s.pet_id, '?')}: {s.task_name} ({state})")
            if next_up:
                lines.append(f"Next up: {next_up.time_of_day} {pet_names.get(next_up.pet_id, '?')}: {next_up.task_name}")
            else:
                lines.append("Next up: nothing else today.")

        if logs:
            lines.append("\n## Recently logged")
            for log in logs[:8]:
                task = schedule_names.get(log.schedule_id, "Activity")
                notes = f" - {log.notes}" if log.notes else ""
                lines.append(
                    f"- {to_local(log.timestamp).strftime('%a %H:%M')} ({ago(now - to_local(log.timestamp))}): "
                    f"{pet_names.get(log.pet_id, '?')} {task} {log.status.value}{notes}"
                )

        context = "\n".join(lines)
        if len(context) / 4 > 20000:
            logger.warning("Household context is over ~20k tokens; consider search instead of sending everything.")
        return context

    def chat(self, user_input: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """Answers a sitter's question using all household knowledge."""
        messages = [{"role": "system", "content": f"{SYSTEM_RULES}\n\n# Household information\n{self.build_context()}"}]
        messages += [{"role": m["role"], "content": m["content"]} for m in (history or [])[-10:]]
        messages.append({"role": "user", "content": user_input})
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception:
            logger.exception("Error in PetAgent.chat")
            return "Sorry, I couldn't reach the assistant right now. Please try again, or contact the owner."

    def log_activity(self, pet_id: int, task_name: str, status: str, notes: Optional[str] = None) -> str:
        """Logs a completed or missed activity in the database."""
        with self.db.get_session() as session:
            schedule_item = session.exec(
                select(Schedule).where(Schedule.pet_id == pet_id, Schedule.task_name == task_name)
            ).first()
            session.add(ActivityLog(
                pet_id=pet_id,
                schedule_id=schedule_item.id if schedule_item else None,
                status=status,
                notes=notes,
            ))
            if schedule_item:
                schedule_item.last_run = datetime.now(timezone.utc)
                session.add(schedule_item)
            session.commit()
            return f"Successfully logged {status} for {task_name}."

    def get_pet_by_name(self, name: str) -> Optional[Pet]:
        """Finds a pet by its name (case-insensitive)."""
        with self.db.get_session() as session:
            return session.exec(select(Pet).where(func.lower(Pet.name) == name.lower())).first()

    def get_pet_info(self, pet_id: int) -> str:
        """Returns basic info about a pet."""
        with self.db.get_session() as session:
            pet = session.get(Pet, pet_id)
            if not pet:
                return "Pet not found."
            return f"Pet: {pet.name}\nDescription: {pet.description}"


if __name__ == "__main__":
    import sys
    agent = PetAgent()
    print(agent.build_context())
    if len(sys.argv) > 1:
        print("\n---\n" + agent.chat(" ".join(sys.argv[1:])))
