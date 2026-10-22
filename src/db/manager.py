from sqlmodel import SQLModel, create_engine, Session
from .models import *
import os

class DatabaseManager:
    def __init__(self, db_url: str = "sqlite:///data/pet_agent.db"):
        self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=False)

    def create_db_and_tables(self):
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)

    def get_session_with_foreign_keys(self) -> Session:
        from sqlalchemy import event

        session = self.get_session()

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return session

    def save_item(self, item: SQLModel):
        with self.get_session_with_foreign_keys() as session:
            session.add(item)
            session.commit()
            session.refresh(item)
            return item

    def get_all(self, model: type[SQLModel]):
        from sqlmodel import select
        with self.get_session_with_foreign_keys() as session:
            statement = select(model)
            results = session.exec(statement)
            return results.all()

    def get_by_id(self, model: type[SQLModel], item_id: int):
        with self.get_session_with_foreign_keys() as session:
            return session.get(model, item_id)

    def delete_item(self, model: type[SQLModel], item_id: int):
        with self.get_session_with_foreign_keys() as session:
            item = session.get(model, item_id)
            if item:
                session.delete(item)
                session.commit()
                return True
            return False
