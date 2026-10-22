import os
import sys

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

import subprocess

def run_dashboard():
    print("Starting Streamlit Dashboard...")
    print("Open http://localhost:8501 in your browser.")
    try:
        root = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([sys.executable, "-m", "streamlit", "run", os.path.join(root, "src/interfaces/dashboard.py"), "--server.address", "0.0.0.0"], check=True, cwd=root)
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    except Exception as e:
        print(f"Error starting dashboard: {e}")

if __name__ == "__main__":
    run_dashboard()
