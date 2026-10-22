import sys
import os
import base64
import re
import html
import mimetypes

# Streamlit only puts this file's folder on the import path; add the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timezone
from src.db.manager import DatabaseManager
from src.db.models import Pet, Schedule, ActivityLog, KnowledgeItem, LogStatus, KnowledgeCategory, to_local

st.set_page_config(page_title="Pawsitter", page_icon="🐾", layout="centered")
load_dotenv()


MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "media"))
PHOTO_TYPES = ["png", "jpg", "jpeg", "gif", "webp"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@400;600;700&display=swap');

:root {
  --cream: #FFF8F0;
  --peach: #FDEBDD;
  --coral: #F2877A;
  --coral-deep: #E06B5D;
  --mint: #CDEFE3;
  --cocoa: #4A3B36;
  --cocoa-soft: #7A6660;
}

html, body, [class*="css"], .stMarkdown, p, li, label, input, textarea {
  font-family: 'Nunito', sans-serif !important;
}
h1, h2, h3, h4, .paw-title, [data-baseweb="tab"] p {
  font-family: 'Fredoka', sans-serif !important;
  color: var(--cocoa);
}

/* Soft dotted background */
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 1px 1px, rgba(242,135,122,0.12) 1.5px, transparent 0) 0 0 / 26px 26px,
    var(--cream);
}
[data-testid="stHeader"] { background: transparent; }

/* Header */
.paw-hero { text-align: center; margin: 0.5rem 0 1.25rem; }
.paw-title { font-size: 2.8rem !important; font-weight: 700; margin: 0; line-height: 1.15; }
.paw-title .paw { display: inline-block; animation: wiggle 2.4s ease-in-out infinite; transform-origin: 50% 80%; }
.paw-sub { color: var(--cocoa-soft); margin-top: 0.35rem; font-size: 1.05rem; }

/* Pet cards */
.pet-row { display: flex; flex-wrap: wrap; justify-content: center; gap: 1.25rem; margin: 0.5rem 0 1.5rem; }
.pet-card {
  background: #fff; border-radius: 24px; padding: 1.1rem 1.4rem 1rem;
  box-shadow: 0 6px 0 var(--peach), 0 10px 24px rgba(74,59,54,0.08);
  text-align: center; min-width: 160px; position: relative;
}
.pet-avatar {
  width: 120px; height: 120px; border-radius: 50%; object-fit: cover;
  border: 5px solid var(--peach); display: block; margin: 0 auto;
  animation: bob 3.2s ease-in-out infinite;
}
/* Hover a pet photo to see it bigger */
.pet-card { transition: z-index 0s; }
.pet-card:hover { z-index: 20; }
img.pet-avatar {
  cursor: zoom-in; position: relative;
  transition: transform 0.35s cubic-bezier(.2,.9,.3,1.3), border-radius 0.35s ease, box-shadow 0.35s ease;
}
img.pet-avatar:hover {
  animation: none;  /* a running or paused animation would override the transform */
  transform: scale(2.6) translateY(18px);
  border-radius: 18px;
  box-shadow: 0 12px 40px rgba(74,59,54,0.35);
  z-index: 30;
}
.pet-avatar.emoji {
  display: flex; align-items: center; justify-content: center;
  font-size: 64px; background: var(--peach);
}
.pet-name { font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.5rem; color: var(--cocoa); margin-top: 0.6rem; }
.pet-desc { color: var(--cocoa-soft); font-size: 0.9rem; max-width: 220px; margin: 0.15rem auto 0; }
.pet-card .heart {
  position: absolute; top: 10px; right: 14px; font-size: 1.1rem;
  animation: beat 1.6s ease-in-out infinite;
}

/* Floating paw prints */
.paw-float { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.paw-float span {
  position: absolute; bottom: -40px; font-size: 22px; opacity: 0;
  animation: floatUp 14s linear infinite;
}
.paw-float span:nth-child(1) { left: 6%;  animation-delay: 0s; }
.paw-float span:nth-child(2) { left: 22%; animation-delay: 4s;  font-size: 16px; }
.paw-float span:nth-child(3) { left: 78%; animation-delay: 2s; }
.paw-float span:nth-child(4) { left: 92%; animation-delay: 7s;  font-size: 18px; }
.paw-float span:nth-child(5) { left: 50%; animation-delay: 10s; font-size: 14px; }

/* Tabs as pills */
[role="tablist"] { gap: 0.6rem; justify-content: center; border: none !important; box-shadow: none !important; }
[role="tablist"]::after, [role="tablist"] > :not([data-testid="stTab"]) { display: none !important; }
[data-testid="stTab"] {
  background: #fff; border-radius: 999px !important; padding: 0.4rem 1.2rem !important;
  box-shadow: 0 3px 0 var(--peach); border: none !important;
}
[data-testid="stTab"] p { font-family: 'Fredoka', sans-serif !important; font-size: 1.05rem !important; }
[data-testid="stTab"][aria-selected="true"] { background: var(--coral); box-shadow: 0 3px 0 var(--coral-deep); }
[data-testid="stTab"][aria-selected="true"] p { color: #fff !important; }

/* Rounded, friendly widgets */
.stButton > button, .stFormSubmitButton > button {
  border-radius: 999px; font-weight: 700; border: 2px solid var(--coral);
  transition: transform 0.15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover { transform: translateY(-2px) scale(1.03); }
[data-testid="stExpander"], [data-testid="stForm"] {
  background: #fff; border-radius: 20px !important; border: none !important;
  box-shadow: 0 4px 0 var(--peach);
}
[data-testid="stChatMessage"] {
  background: #fff; border-radius: 20px; box-shadow: 0 3px 0 var(--peach);
  animation: popIn 0.35s ease-out;
}
[data-testid="stChatInput"] textarea { border-radius: 999px; }

@keyframes bob    { 0%,100% { transform: translateY(0) rotate(-2deg); } 50% { transform: translateY(-7px) rotate(2deg); } }
@keyframes wiggle { 0%,100% { transform: rotate(0); } 20% { transform: rotate(-14deg); } 40% { transform: rotate(10deg); } 60% { transform: rotate(-6deg); } 80% { transform: rotate(0); } }
@keyframes beat   { 0%,100% { transform: scale(1); } 15% { transform: scale(1.25); } 30% { transform: scale(1); } 45% { transform: scale(1.18); } }
@keyframes floatUp { 0% { transform: translateY(0) rotate(0); opacity: 0; } 10% { opacity: 0.35; } 90% { opacity: 0.25; } 100% { transform: translateY(-110vh) rotate(40deg); opacity: 0; } }
@keyframes popIn  { from { transform: scale(0.96); opacity: 0; } to { transform: scale(1); opacity: 1; } }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
<div class="paw-float"><span>🐾</span><span>🐾</span><span>🐾</span><span>🐾</span><span>🐾</span></div>
"""


def save_upload(upload) -> str:
    """Saves an uploaded file into media/ and returns its path."""
    os.makedirs(MEDIA_DIR, exist_ok=True)
    safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(upload.name)}"
    path = os.path.join(MEDIA_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(upload.getbuffer())
    return path


def image_data_uri(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


STOPWORDS = {"and", "the", "for", "with", "his", "her", "their", "favorite", "if", "what", "where", "how"}


def stem_words(text: str) -> set:
    """Lowercase words with crude plural/-ing stripping, so 'toys' matches 'toy'."""
    words = set()
    for word in re.findall(r"[a-z]+", text.lower().replace("'s", "")):
        for suffix in ("ing", "es", "s"):
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                word = word[: -len(suffix)]
                break
        words.add(word)
    return words


def related_photos(db, question: str, answer: str, limit: int = 2) -> list:
    """Photos for knowledge items whose topic matches the question (or, less strongly, the answer)."""
    pets = db.get_all(Pet)
    pet_names = {p.name.lower() for p in pets}
    asked_pets = {p.id for p in pets if p.name.lower() in question.lower()}
    q_words, a_words = stem_words(question), stem_words(answer)

    scored = []
    for item in db.get_all(KnowledgeItem):
        if not (item.media_path and os.path.exists(item.media_path)):
            continue
        if asked_pets and item.pet_id and item.pet_id not in asked_pets:
            continue
        keywords = {w for w in stem_words(item.query) if len(w) >= 3} - STOPWORDS - pet_names
        score = 2 * len(keywords & q_words) + len(keywords & a_words)
        if keywords & q_words or score >= 2:
            scored.append((score, item))
    scored.sort(key=lambda pair: -pair[0])
    return [{"path": i.media_path, "caption": i.query} for _, i in scored[:limit]]


@st.cache_resource
def get_agent():
    from src.core.agent import PetAgent
    return PetAgent()


class DashboardApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.db.create_db_and_tables()

    def run(self):
        st.markdown(CSS, unsafe_allow_html=True)
        st.markdown(
            '<div class="paw-hero">'
            '<div class="paw-title"><span class="paw">🐾</span> Pawsitter</div>'
            '<div class="paw-sub">Everything you need to look after your furry friends</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        sitter_tab, owner_tab = st.tabs(["🏡 Sitter", "🔒 Owner"])

        with sitter_tab:
            self.render_pet_cards()
            self.render_sitter_chat()
            self.render_sitter_view()

        with owner_tab:
            if self.owner_unlocked():
                self.render_owner_view()

    def render_pet_cards(self):
        pets = self.db.get_all(Pet)
        if not pets:
            st.info("No pets yet. Add one in the Owner tab! 🐶🐱")
            return
        cards = []
        for pet in pets:
            if pet.photo_path and os.path.exists(pet.photo_path):
                avatar = f'<img class="pet-avatar" src="{image_data_uri(pet.photo_path)}" alt="{html.escape(pet.name)}">'
            else:
                avatar = '<div class="pet-avatar emoji">🐾</div>'
            desc = f'<div class="pet-desc">{html.escape(pet.description)}</div>' if pet.description else ""
            cards.append(
                f'<div class="pet-card"><span class="heart">💗</span>{avatar}'
                f'<div class="pet-name">{html.escape(pet.name)}</div>{desc}</div>'
            )
        st.markdown(f'<div class="pet-row">{"".join(cards)}</div>', unsafe_allow_html=True)

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
        st.subheader("💬 Ask me anything")
        history = st.session_state.setdefault("chat_history", [])
        for msg in history:
            with st.chat_message(msg["role"], avatar="🐾" if msg["role"] == "assistant" else "🧑"):
                st.write(msg["content"])
                for photo in msg.get("photos", []):
                    st.image(photo["path"], caption=photo["caption"], width=300)

        question = st.chat_input("e.g. How much Ondansetron does Sonic get?")
        if question:
            with st.chat_message("user", avatar="🧑"):
                st.write(question)
            with st.chat_message("assistant", avatar="🐾"):
                with st.spinner("Sniffing out the answer... 🐾"):
                    answer = get_agent().chat(question, history)
                st.write(answer)
                photos = related_photos(self.db, question, answer)
                for photo in photos:
                    st.image(photo["path"], caption=photo["caption"], width=300)
            history += [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer, "photos": photos},
            ]

        if history and st.button("🧹 Clear chat"):
            st.session_state.chat_history = []
            st.rerun()

    def render_owner_view(self):
        section = st.radio(
            "Manage",
            ["🐾 Pets", "⏰ Schedules", "📚 Knowledge", "📝 Activity"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if section.endswith("Pets"):
            self.manage_pets()
        elif section.endswith("Schedules"):
            self.manage_schedules()
        elif section.endswith("Knowledge"):
            self.manage_knowledge()
        else:
            self.render_activity_logs()

    def manage_pets(self):
        st.subheader("Your pets")

        with st.expander("➕ Add a new pet"):
            with st.form("add_pet_form", clear_on_submit=True):
                new_pet_name = st.text_input("Pet name")
                new_pet_desc = st.text_area("About them (species, personality, quirks)")
                new_pet_photo = st.file_uploader("Photo", type=PHOTO_TYPES)
                submit_pet = st.form_submit_button("Add pet 🐾")

                if submit_pet and new_pet_name:
                    photo_path = save_upload(new_pet_photo) if new_pet_photo else None
                    self.db.save_item(Pet(name=new_pet_name, description=new_pet_desc, photo_path=photo_path))
                    st.toast(f"Welcome, {new_pet_name}! 🎉")
                    st.rerun()

        pets = self.db.get_all(Pet)
        if not pets:
            st.info("No pets found. Add one above!")
            return
        for pet in pets:
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])
                with col1:
                    if pet.photo_path and os.path.exists(pet.photo_path):
                        st.image(pet.photo_path, width=110)
                    else:
                        st.markdown("<div style='font-size:64px;text-align:center'>🐾</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"### {pet.name}")
                    if pet.description:
                        st.caption(pet.description)
                    new_photo = st.file_uploader(
                        f"Change {pet.name}'s photo", type=PHOTO_TYPES, key=f"photo_{pet.id}"
                    )
                    b1, b2 = st.columns(2)
                    with b1:
                        if new_photo and st.button("Save photo", key=f"save_photo_{pet.id}"):
                            pet.photo_path = save_upload(new_photo)
                            self.db.save_item(pet)
                            st.toast(f"Looking good, {pet.name}! 📸")
                            st.rerun()
                    with b2:
                        if st.button("Delete", key=f"del_pet_{pet.id}"):
                            self.db.delete_item(Pet, pet.id)
                            st.rerun()

    def manage_schedules(self):
        st.subheader("Schedules")
        pets = self.db.get_all(Pet)
        if not pets:
            st.warning("Add a pet first!")
            return

        with st.expander("➕ Add a schedule"):
            with st.form("add_schedule_form", clear_on_submit=True):
                target_pet_name = st.selectbox("Pet", [p.name for p in pets])
                task_name = st.text_input("Task (e.g., Feeding)")
                task_desc = st.text_area("Details")
                task_time = st.time_input("Time", value=datetime.strptime("08:00", "%H:%M").time())
                task_freq = st.selectbox("Frequency", ["daily", "weekly"])
                submit_sched = st.form_submit_button("Add schedule ⏰")

                if submit_sched and target_pet_name and task_name:
                    target_pet = next(p for p in pets if p.name == target_pet_name)
                    self.db.save_item(Schedule(
                        pet_id=target_pet.id,
                        task_name=task_name,
                        description=task_desc,
                        time_of_day=task_time.strftime("%H:%M"),
                        frequency=task_freq,
                    ))
                    st.toast("Schedule added! ⏰")
                    st.rerun()

        pet_names = {p.id: p.name for p in pets}
        for s in sorted(self.db.get_all(Schedule), key=lambda s: s.time_of_day):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{s.time_of_day}** · {pet_names.get(s.pet_id, 'Unknown')} · {s.task_name} ({s.frequency})")
            with col2:
                if st.button("Delete", key=f"del_sched_{s.id}"):
                    self.db.delete_item(Schedule, s.id)
                    st.rerun()

    def manage_knowledge(self):
        st.subheader("Household knowledge")

        with st.expander("➕ Add knowledge"):
            with st.form("add_knowledge_form", clear_on_submit=True):
                query_text = st.text_input("Topic (e.g., 'Treats' or 'Methimazole')")
                content_text = st.text_area("What the sitter should know")
                category = st.selectbox("Category", [k.value for k in KnowledgeCategory])

                pets = self.db.get_all(Pet)
                target_pet_name = st.selectbox("Pet (optional)", ["None"] + [p.name for p in pets])
                photo = st.file_uploader("Photo (optional) – shown when the sitter asks about this topic", type=PHOTO_TYPES)

                submit_knowledge = st.form_submit_button("Add knowledge 📚")

                if submit_knowledge and query_text and content_text:
                    target_pet_id = None
                    if target_pet_name != "None":
                        target_pet_id = next(p for p in pets if p.name == target_pet_name).id

                    self.db.save_item(KnowledgeItem(
                        query=query_text,
                        content=content_text,
                        category=KnowledgeCategory(category),
                        pet_id=target_pet_id,
                        media_path=save_upload(photo) if photo else None,
                    ))
                    st.toast("Knowledge added! 📚")
                    st.rerun()

        items = self.db.get_all(KnowledgeItem)
        if not items:
            st.info("No knowledge items found.")
            return
        for item in items:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{item.query}** · {item.category.value}")
                    st.caption(item.content[:140] + ("..." if len(item.content) > 140 else ""))
                    if item.media_path and os.path.exists(item.media_path):
                        st.image(item.media_path, width=150)
                    else:
                        new_photo = st.file_uploader("Add a photo", type=PHOTO_TYPES, key=f"kphoto_{item.id}")
                        if new_photo and st.button("Save photo", key=f"save_kphoto_{item.id}"):
                            item.media_path = save_upload(new_photo)
                            self.db.save_item(item)
                            st.rerun()
                with col2:
                    if st.button("Delete", key=f"del_know_{item.id}"):
                        self.db.delete_item(KnowledgeItem, item.id)
                        st.rerun()

    def render_activity_logs(self):
        st.subheader("Activity history")
        logs = self.db.get_all(ActivityLog)
        if not logs:
            st.info("No activity logged yet.")
            return
        pet_names = {p.id: p.name for p in self.db.get_all(Pet)}
        for log in sorted(logs, key=lambda x: x.timestamp, reverse=True):
            st.write(
                f"**{to_local(log.timestamp).strftime('%a %b %d, %H:%M')}** · "
                f"{pet_names.get(log.pet_id, 'Unknown')} · {log.status.value}"
            )
            if log.notes:
                st.caption(f"Note: {log.notes}")

    def render_sitter_view(self):
        st.subheader("✅ Today's checklist")
        pets = self.db.get_all(Pet)
        if not pets:
            return

        today = datetime.now().astimezone().date()
        done_ids = {
            log.schedule_id for log in self.db.get_all(ActivityLog)
            if log.schedule_id and to_local(log.timestamp).date() == today
        }
        schedules = self.db.get_all(Schedule)

        for pet in pets:
            pet_schedules = sorted((s for s in schedules if s.pet_id == pet.id), key=lambda s: s.time_of_day)
            with st.expander(f"🐾 {pet.name}'s tasks", expanded=True):
                if not pet_schedules:
                    st.write("No tasks scheduled. Enjoy the cuddles! 💤")
                    continue
                for s in pet_schedules:
                    col1, col2 = st.columns([4, 1])
                    done = s.id in done_ids
                    with col1:
                        label = f"~~{s.task_name}~~" if done else f"**{s.task_name}**"
                        st.write(f"{label} · {s.time_of_day}")
                        if s.description:
                            st.caption(s.description)
                    with col2:
                        if done:
                            st.write("✅ Done")
                        elif st.button("Done", key=f"done_sched_{s.id}"):
                            self.db.save_item(ActivityLog(
                                pet_id=pet.id,
                                schedule_id=s.id,
                                status=LogStatus.COMPLETED,
                            ))
                            st.session_state.celebrate = f"{s.task_name} done for {pet.name}! 🎉"
                            st.rerun()

        if msg := st.session_state.pop("celebrate", None):
            st.toast(msg)
            st.balloons()


if __name__ == "__main__":
    app = DashboardApp()
    app.run()
