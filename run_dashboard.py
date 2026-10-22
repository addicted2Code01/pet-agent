import os
import sys

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

import subprocess

def run_dashboard():
    print("Starting Streamlit Dashboard...")
    print("Open http://localhost:8501 in your browser.")
    try:
        subprocess.run(["streamlit", "run", "src/interfaces/dashboard.py"], check=True)
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    except Exception as e:
        print(f"Error starting dashboard: {e}")

if __name__ == "__main__":
    run_dashboard()
