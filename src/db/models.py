from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime, timezone
import enum

class LogStatus(str, enum.Enum):
    COMPLETED = "completed"
    MISSED = "missed"
    PENDING = "pending"

class KnowledgeCategory(str, enum.Enum):
    LOCATION = "location"
    EMERGENCY = "emergency"
    INSTRUCTION = "instruction"
    GENERAL = "general"

class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"

class Pet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    schedules: List["Schedule"] = Relationship(back_populates="pet")
    logs: List["ActivityLog"] = Relationship(back_populates="pet")
    knowledge_items: List["KnowledgeItem"] = Relationship(back_populates="pet")

class Schedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pet_id: int = Field(foreign_key="pet.id")
    task_name: str
    description: Optional[str] = None
    time_of_day: str  # Format HH:MM
    frequency: str = "daily"
    last_run: Optional[datetime] = Field(default=None)

    # Relationships
    pet: Pet = Relationship(back_populates="schedules")
    logs: List["ActivityLog"] = Relationship(back_populates="schedule")

class ActivityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pet_id: int = Field(foreign_key="pet.id")
    schedule_id: Optional[int] = Field(default=None, foreign_key="schedule.id")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: LogStatus = Field(default=LogStatus.PENDING)
    notes: Optional[str] = None

    # Relationships
    pet: Pet = Relationship(back_populates="logs")
    schedule: Optional[Schedule] = Relationship(back_populates="logs")

class KnowledgeItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pet_id: Optional[int] = Field(default=None, foreign_key="pet.id")
    category: KnowledgeCategory = Field(default=KnowledgeCategory.GENERAL)
    query: str = Field(index=True)
    content: str
    media_path: Optional[str] = None

    # Relationships
    pet: Optional[Pet] = Relationship(back_populates="knowledge_items")

class Media(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    file_path: str
    media_type: MediaType
    description: Optional[str] = None
