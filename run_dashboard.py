#!/usr/bin/env python
"""
Quick launcher for the Streamlit dashboard.
Usage: python run_dashboard.py
"""
import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/aiops_sre/streamlit_app.py"])
