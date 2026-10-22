# 🐾 Pawsitter

A private, local-first AI assistant that helps pet sitters follow the owner's instructions: medications, feeding, schedules and where everything is.

The sitter opens the dashboard on their phone (on the home Wi-Fi) and asks things like *"How much Ondansetron does Sonic get?"* or *"What do I need to do next?"*. Answers come from a local LLM using only the owner's own notes, with photos of the right pill bottle or pen. Nothing leaves the home network.

## Features
- **Ask anything:** chat with a local LLM that answers only from the household's information and says "I don't know, contact the owner" instead of guessing.
- **Knows the time:** the current time, overdue and upcoming tasks and recent activity are in every prompt, so "what's next?" just works.
- **Photos in answers:** knowledge items can have photos (the real medication pen, the cat food can) shown alongside matching answers.
- **Daily checklist:** tap "Done" on each task (with balloons 🎉); the owner sees the activity history.
- **Owner view:** manage pets (with photos), schedules and household knowledge; optionally password-protected.

## Why local-first
Pet care notes include medication doses, home layout and door codes. Pawsitter runs an LLM on the owner's own machine (llama.cpp's `llama-server`) and serves the dashboard on the local network only. The whole knowledge base is sent with each question instead of using vector search, so medication instructions are never missed.

## Tech
Python, Streamlit, SQLite/SQLModel, OpenAI-compatible API to a local `llama-server` running Gemma.

## Run it
1. Start a local OpenAI-compatible LLM server, for example:
   ```bash
   llama-server -m your-model.gguf --jinja --port 8080
   ```
2. Install and configure:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env   # set LLM_BASE_URL=http://localhost:8080/v1 and, optionally, OWNER_PASSWORD
   ```
3. Seed data and start the dashboard:
   ```bash
   python3 scripts/init_db.py      # Sonic and his medication list
   python3 scripts/seed_demo.py    # optional demo data for every section
   python3 run_dashboard.py        # http://localhost:8501 (or your Mac's LAN IP from a phone)
   ```

## Credits
Demo photos are from Wikimedia Commons; see [assets/demo/CREDITS.md](assets/demo/CREDITS.md). Built with help from Claude Code.
