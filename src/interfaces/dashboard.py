import sys
import os

# Streamlit only puts this file's folder on the import path; add the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from src.db.manager import DatabaseManager
from src.db.models import Pet, Schedule, ActivityLog, KnowledgeItem, LogStatus, KnowledgeCategory

# Set page config
st.set_page_config(page_title="Pet Sitter AI Dashboard", layout="centered")
load_dotenv()


MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "media"))


def related_photos(db, text: str) -> list:
    """Photos for knowledge items whose topic is mentioned in the question or answer."""
    text = text.lower()
    photos = []
    for item in db.get_all(KnowledgeItem):
        topic = item.query.split("(")[0].strip().lower()
        if item.media_path and os.path.exists(item.media_path) and topic and topic in text:
            photos.append({"path": item.media_path, "caption": item.query})
    return photos


@st.cache_resource
def get_agent():
    from src.core.agent import PetAgent
    return PetAgent()

class DashboardApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.db.create_db_and_tables()

    def run(self):
        st.title("🐾 Pet Sitter AI Dashboard")
        
        sitter_tab, owner_tab = st.tabs(["Sitter View", "Owner View (Management)"])

        with sitter_tab:
            self.render_sitter_chat()
            self.render_sitter_view()

        with owner_tab:
            if self.owner_unlocked():
                self.render_owner_view()

    def owner_unlocked(self) -> bool:
        password = os.getenv("OWNER_PASSWORD")
        if not password or st.session_state.get("owner_ok"):
            return True
        entered = st.text_input("Owner password", type="password")
        if entered == password:
            st.session_state.owner_ok = True
            st.rerun()
        elif entered:
            st.error("Wrong password.")
        return False

    def render_sitter_chat(self):
        st.header("Ask about the pets")
        history = st.session_state.setdefault("chat_history", [])
        for msg in history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                for photo in msg.get("photos", []):
                    st.image(photo["path"], caption=photo["caption"], width=300)

        question = st.chat_input("e.g. How much Ondansetron does Sonic get?")
        if question:
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = get_agent().chat(question, history)
                st.write(answer)
                photos = related_photos(self.db, f"{question} {answer}")
                for photo in photos:
                    st.image(photo["path"], caption=photo["caption"], width=300)
            history += [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer, "photos": photos},
            ]

        if history and st.button("Clear chat"):
            st.session_state.chat_history = []
            st.rerun()

    def render_owner_view(self):
        st.header("Owner Management")
        
        # Sidebar or sub-sections for different management areas
        menu = st.sidebar.selectbox("Management Menu", ["Pets", "Schedules", "Knowledge Base", "Activity Logs"])

        if menu == "Pets":
            self.manage_pets()
        elif menu == "Schedules":
            self.manage_schedules()
        elif menu == "Knowledge Base":
            self.manage_knowledge()
        elif menu == "Activity Logs":
            self.render_activity_logs()

    def manage_pets(self):
        st.subheader("Manage Pets")
        
        # Form to add a new pet
        with st.expander("➕ Add New Pet"):
            with st.form("add_pet_form"):
                new_pet_name = st.text_input("Pet Name")
                new_pet_desc = st.text_area("Description")
                submit_pet = st.form_submit_button("Add Pet")
                
                if submit_pet and new_pet_name:
                    new_pet = Pet(name=new_pet_name, description=new_pet_desc)
                    self.db.save_item(new_pet)
                    st.success(f"Added {new_pet_name}!")
                    st.rerun()

        # List existing pets
        pets = self.db.get_all(Pet)
        if pets:
            for pet in pets:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{pet.name}** - {pet.description}")
                with col2:
                    if st.button(f"Delete", key=f"del_pet_{pet.id}"):
                        self.db.delete_item(Pet, pet.id)
                        st.rerun()
        else:
            st.info("No pets found. Add one above!")

    def manage_schedules(self):
        st.subheader("Manage Schedules")
        pets = self.db.get_all(Pet)
        if not pets:
            st.warning("Add a pet first!")
            return

        # Form to add a schedule
        with st.expander("➕ Add New Schedule"):
            with st.form("add_schedule_form"):
                target_pet_name = st.selectbox("Select Pet", [p.name for p in pets])
                task_name = st.text_input("Task Name (e.g., Feeding)")
                task_desc = st.text_area("Task Description")
                task_time = st.text_input("Time (HH:MM)", value="08:00")
                task_freq = st.selectbox("Frequency", ["daily", "weekly"])
                submit_sched = st.form_submit_button("Add Schedule")

                if submit_sched and target_pet_name and task_name:
                    target_pet = next(p for p in pets if p.name == target_pet_name)
                    new_sched = Schedule(
                        pet_id=target_pet.id,
                        task_name=task_name,
                        description=task_desc,
                        time_of_day=task_time,
                        frequency=task_freq
                    )
                    self.db.save_item(new_sched)
                    st.success("Schedule added!")
                    st.rerun()

        # List existing schedules
        st.write("### Current Schedules")
        all_schedules = self.db.get_all(Schedule)
        for s in all_schedules:
            # Find pet name
            pet = self.db.get_by_id(Pet, s.pet_id)
            pet_name = pet.name if pet else "Unknown"
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**[{pet_name}]** {s.task_name} at {s.time_of_day} ({s.frequency})")
            with col2:
                if st.button("Delete", key=f"del_sched_{s.id}"):
                    self.db.delete_item(Schedule, s.id)
                    st.rerun()

    def manage_knowledge(self):
        st.subheader("Knowledge Base")
        
        # Form to add a new knowledge item
        with st.expander("➕ Add New Knowledge Item"):
            with st.form("add_knowledge_form"):
                query_text = st.text_input("Searchable Query (e.g., 'Where are the treats?')")
                content_text = st.text_area("Information Content")
                category = st.selectbox("Category", [k.value for k in KnowledgeCategory])
                
                # Pet selection
                pets = self.db.get_all(Pet)
                target_pet_name = st.selectbox("Associated Pet (Optional)", ["None"] + [p.name for p in pets])
                
                photo = st.file_uploader("Photo (optional)", type=["png", "jpg", "jpeg", "gif", "webp"])

                submit_knowledge = st.form_submit_button("Add Knowledge")

                if submit_knowledge and query_text and content_text:
                    target_pet_id = None
                    if target_pet_name != "None":
                        target_pet = next(p for p in pets if p.name == target_pet_name)
                        target_pet_id = target_pet.id
                    
                    media_path = None
                    if photo:
                        os.makedirs(MEDIA_DIR, exist_ok=True)
                        safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(photo.name)}"
                        media_path = os.path.join(MEDIA_DIR, safe_name)
                        with open(media_path, "wb") as f:
                            f.write(photo.getbuffer())

                    new_item = KnowledgeItem(
                        query=query_text,
                        content=content_text,
                        category=KnowledgeCategory(category),
                        pet_id=target_pet_id,
                        media_path=media_path
                    )
                    self.db.save_item(new_item)
                    st.success("Knowledge item added!")
                    st.rerun()

        # List existing knowledge items
        st.write("### Existing Knowledge")
        items = self.db.get_all(KnowledgeItem)
        if not items:
            st.info("No knowledge items found.")
        else:
            for item in items:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{item.query}** ({item.category.value})")
                        st.caption(item.content[:100] + ("..." if len(item.content) > 100 else ""))
                        if item.media_path and os.path.exists(item.media_path):
                            st.image(item.media_path, width=150)
                    with col2:
                        if st.button("Delete", key=f"del_know_{item.id}"):
                            self.db.delete_item(KnowledgeItem, item.id)
                            st.rerun()
                    st.divider()

    def render_activity_logs(self):
        st.subheader("Activity History")
        logs = self.db.get_all(ActivityLog)
        if not logs:
            st.info("No activity logged yet.")
        else:
            # Sort logs by timestamp descending
            sorted_logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)
            for log in sorted_logs:
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 2])
                    with col1:
                        st.write(f"**{log.timestamp.strftime('%Y-%m-%d %H:%M')}**")
                    with col2:
                        pet = self.db.get_by_id(Pet, log.pet_id)
                        st.write(f"{pet.name if pet else 'Unknown'}")
                    with col3:
                        st.write(f"Status: {log.status.value}")
                    if log.notes:
                        st.caption(f"Note: {log.notes}")
                    st.divider()

    def render_sitter_view(self):
        st.header("Today's Checklist")
        pets = self.db.get_all(Pet)
        
        if not pets:
            st.info("No pets found.")
            return

        for pet in pets:
            with st.expander(f"📋 {pet.name}'s Tasks", expanded=True):
                schedules = self.db.get_all(Schedule)
                pet_schedules = [s for s in schedules if s.pet_id == pet.id]
                
                if not pet_schedules:
                    st.write("No tasks scheduled.")
                else:
                    for s in pet_schedules:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"**{s.task_name}** ({s.time_of_day})")
                            if s.description:
                                st.caption(s.description)
                        with col2:
                            if st.button("Done", key=f"done_sched_{s.id}"):
                                self.db.save_item(ActivityLog(
                                    pet_id=pet.id,
                                    schedule_id=s.id,
                                    status=LogStatus.COMPLETED
                                ))
                                st.success("Logged!")
                                st.rerun()

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
