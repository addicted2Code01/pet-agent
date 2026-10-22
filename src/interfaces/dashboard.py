import streamlit as st
import os
from datetime import datetime
from src.db.manager import DatabaseManager
from src.db.models import Pet, Schedule, ActivityLog, KnowledgeItem, LogStatus, KnowledgeCategory

# Set page config
st.set_page_config(page_title="Pet Sitter AI Dashboard", layout="wide")

class DashboardApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.db.create_db_and_tables()

    def run(self):
        st.title("🐾 Pet Sitter AI Dashboard")
        
        tab1, tab2 = st.tabs(["Owner View (Management)", "Sitter View (Daily Tasks)"])

        with tab1:
            self.render_owner_view()
        
        with tab2:
            self.render_sitter_view()

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
        
        # Import RAG service here to avoid circular imports if needed
        from src.core.rag_service import RAGService
        rag = RAGService()

        # Rebuild Button
        if st.button("🔄 Rebuild Vector Index (Sync with DB)"):
            with st.spinner("Rebuilding index..."):
                rag.rebuild_index()
                st.success("Index rebuilt successfully!")
                st.rerun()

        # Form to add a new knowledge item
        with st.expander("➕ Add New Knowledge Item"):
            with st.form("add_knowledge_form"):
                query_text = st.text_input("Searchable Query (e.g., 'Where are the treats?')")
                content_text = st.text_area("Information Content")
                category = st.selectbox("Category", [k.value for k in KnowledgeCategory])
                
                # Pet selection
                pets = self.db.get_all(Pet)
                target_pet_name = st.selectbox("Associated Pet (Optional)", ["None"] + [p.name for p in pets])
                
                submit_knowledge = st.form_submit_button("Add Knowledge")

                if submit_knowledge and query_text and content_text:
                    target_pet_id = None
                    if target_pet_name != "None":
                        target_pet = next(p for p in pets if p.name == target_pet_name)
                        target_pet_id = target_pet.id
                    
                    new_item = KnowledgeItem(
                        query=query_text,
                        content=content_text,
                        category=KnowledgeCategory(category),
                        pet_id=target_pet_id
                    )
                    self.db.save_item(new_item)
                    st.success("Knowledge item added! Remember to rebuild the index.")
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
