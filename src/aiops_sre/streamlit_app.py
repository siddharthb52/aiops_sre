"""
Streamlit UI for real-time AIOps/SRE monitoring.
Shows incoming logs, agent recommendations, and fleet health status.
"""
import streamlit as st
import time
import json
from pathlib import Path
from datetime import datetime
import threading
from typing import Optional

from aiops_sre.log_generator import LogGenerator
from aiops_sre.crew import AiopsSreCrew


# Page config
st.set_page_config(
    page_title="AIOps SRE Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and terminal-style logs
st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Terminal-style log container */
    .terminal-log {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 12px;
        font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
        font-size: 13px;
        line-height: 1.6;
        max-height: 600px;
        overflow-y: auto;
        color: #d4d4d4;
    }
    
    /* Custom scrollbar for terminal */
    .terminal-log::-webkit-scrollbar {
        width: 8px;
    }
    
    .terminal-log::-webkit-scrollbar-track {
        background: #1e1e1e;
    }
    
    .terminal-log::-webkit-scrollbar-thumb {
        background: #555;
        border-radius: 4px;
    }
    
    .terminal-log::-webkit-scrollbar-thumb:hover {
        background: #666;
    }
    
    /* Log entry styles */
    .log-entry {
        margin: 2px 0;
        padding: 2px 0;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .log-info { color: #4ec9b0; }
    .log-warn { color: #dcdcaa; }
    .log-critical { color: #f48771; }
    
    /* Remove default Streamlit box styling */
    .stAlert, .stInfo, .stWarning, .stError {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Status indicators */
    .status-running { color: #4ec9b0; }
    .status-stopped { color: #808080; }
    .status-ready { color: #4ec9b0; }
    .status-processing { color: #dcdcaa; }
    
    /* Headers */
    h1, h2, h3 {
        color: #fafafa !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #262730;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "log_generator" not in st.session_state:
    st.session_state.log_generator = None
if "last_log_count" not in st.session_state:
    st.session_state.last_log_count = 0
if "last_analysis_time" not in st.session_state:
    st.session_state.last_analysis_time = None
if "log_entries" not in st.session_state:
    st.session_state.log_entries = []
if "crew_running" not in st.session_state:
    st.session_state.crew_running = False


def parse_log_entry(entry: str) -> Optional[dict]:
    """Parse a JSON log entry."""
    try:
        return json.loads(entry)
    except:
        return None


def format_log_entry_html(entry: dict) -> str:
    """Format a log entry for terminal-style HTML display."""
    ts = entry.get("ts", "N/A")
    host = entry.get("host", "N/A")
    level = entry.get("level", "INFO")
    cpu = entry.get("cpu", 0)
    mem = entry.get("mem", 0)
    disk = entry.get("disk", 0)
    temp = entry.get("temp_f", 0)
    code = entry.get("code", "")
    msg = entry.get("msg", "")
    
    # Terminal-style formatting
    level_prefix = {
        "INFO": "[INFO]",
        "WARN": "[WARN]",
        "CRITICAL": "[CRIT]"
    }.get(level, "[INFO]")
    
    # Color class based on level
    color_class = {
        "INFO": "log-info",
        "WARN": "log-warn",
        "CRITICAL": "log-critical"
    }.get(level, "log-info")
    
    # Format: [timestamp] [LEVEL] host | CPU: X% | Mem: X% | Disk: X% | Temp: X°F | code | message
    formatted = f"[{ts}] {level_prefix} {host} | CPU: {cpu}% | Mem: {mem}% | Disk: {disk}% | Temp: {temp}°F"
    if code:
        formatted += f" | {code}"
    formatted += f" | {msg}"
    
    return f'<div class="log-entry {color_class}">{formatted}</div>'


def read_incident_report() -> tuple[str, bool]:
    """Read the latest incident report. Returns (content, exists)."""
    report_file = Path("incident_report.md")
    if report_file.exists() and report_file.stat().st_size > 0:
        return report_file.read_text(encoding="utf-8"), True
    return "No incident report available yet.", False


def read_fleet_summary() -> tuple[str, bool]:
    """Read the latest fleet summary. Returns (content, exists)."""
    summary_file = Path("fleet_summary.md")
    if summary_file.exists() and summary_file.stat().st_size > 0:
        return summary_file.read_text(encoding="utf-8"), True
    return "No fleet summary available yet.", False


def run_crew_analysis(log_path: str):
    """Run crew analysis in background."""
    try:
        st.session_state.crew_running = True
        crew = AiopsSreCrew().crew()
        result = crew.kickoff(inputs={"log_path": log_path})
        st.session_state.last_analysis_time = datetime.now()
        st.session_state.crew_running = False
        return result
    except Exception as e:
        st.error(f"Error running crew analysis: {e}")
        st.session_state.crew_running = False
        return None


# Sidebar controls
with st.sidebar:
    st.header("Controls")
    
    # Log generator controls
    st.subheader("Log Generator")
    
    interval = st.slider("Log Interval (seconds)", 0.5, 10.0, 2.0, 0.5)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start", disabled=st.session_state.log_generator is not None and st.session_state.log_generator.running, use_container_width=True):
            if st.session_state.log_generator is None:
                st.session_state.log_generator = LogGenerator(
                    source_file="logs_source.jsonl",
                    target_file="fleet_health.log",
                    interval_seconds=interval
                )
            else:
                st.session_state.log_generator.interval_seconds = interval
            
            # Clear log file and reset state when starting
            log_path = Path("fleet_health.log")
            if log_path.exists():
                log_path.write_text("")
            
            st.session_state.last_log_count = 0
            st.session_state.log_entries = []
            
            # Clear agent report files
            Path("incident_report.md").unlink(missing_ok=True)
            Path("fleet_summary.md").unlink(missing_ok=True)
            
            st.session_state.log_generator.start()
            st.rerun()
    
    with col2:
        if st.button("Stop", disabled=st.session_state.log_generator is None or not st.session_state.log_generator.running, use_container_width=True):
            if st.session_state.log_generator:
                st.session_state.log_generator.stop()
            st.rerun()
    
    if st.button("Reset", use_container_width=True):
        if st.session_state.log_generator:
            st.session_state.log_generator.reset()
        st.session_state.last_log_count = 0
        st.session_state.log_entries = []
        st.session_state.last_analysis_time = None
        
        # Clear agent report files
        Path("incident_report.md").unlink(missing_ok=True)
        Path("fleet_summary.md").unlink(missing_ok=True)
        
        st.rerun()
    
    # Generator status
    if st.session_state.log_generator:
        status = st.session_state.log_generator.get_status()
        status_text = "Running" if status['running'] else "Stopped"
        status_class = "status-running" if status['running'] else "status-stopped"
        st.markdown(f'<p class="{status_class}"><strong>Status:</strong> {status_text}<br>'
                   f'<strong>Progress:</strong> {status["progress"]}<br>'
                   f'<strong>Interval:</strong> {status["interval_seconds"]}s</p>', unsafe_allow_html=True)
    
    st.divider()
    
    # Analysis controls
    st.subheader("Analysis")
    
    auto_analyze = st.checkbox("Auto-analyze on new logs", value=True)
    analysis_interval = st.slider("Analysis Interval (seconds)", 5, 60, 10, 5)
    
    if st.button("Run Analysis Now", disabled=st.session_state.crew_running, use_container_width=True):
        with st.spinner("Running crew analysis..."):
            run_crew_analysis("fleet_health.log")
        st.rerun()


# Main content
st.title("AIOps SRE Dashboard")
st.markdown("Real-time fleet health monitoring and incident analysis")

# Create columns for the panes
col1, col2 = st.columns([1.2, 1])

# Pane 1: Incoming Logs
with col1:
    st.header("Incoming Logs")
    
    log_path = "fleet_health.log"
    log_file = Path(log_path)
    
    # Read and process logs
    if log_file.exists():
        all_lines = log_file.read_text(encoding="utf-8").splitlines()
        current_log_count = len(all_lines)
        
        # Process new logs
        if current_log_count > st.session_state.last_log_count:
            new_lines = all_lines[st.session_state.last_log_count:]
            for line in new_lines:
                parsed = parse_log_entry(line)
                if parsed:
                    # Only add if not already in our entries
                    if not any(e.get("raw") == line for e in st.session_state.log_entries):
                        st.session_state.log_entries.append({
                            "timestamp": datetime.now(),
                            "data": parsed,
                            "raw": line
                        })
            
            st.session_state.last_log_count = current_log_count
    
    # Display log entries in terminal style (most recent first)
    display_entries = st.session_state.log_entries[-100:] if len(st.session_state.log_entries) > 100 else st.session_state.log_entries
    
    # Build HTML for all log entries
    if display_entries:
        log_html = '<div class="terminal-log">'
        for entry in reversed(display_entries):
            log_html += format_log_entry_html(entry["data"])
        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)
    else:
        # Show empty terminal
        st.markdown('<div class="terminal-log"><div class="log-entry" style="color: #808080;">No logs yet. Start the log generator to begin monitoring.</div></div>', unsafe_allow_html=True)
    
    st.caption(f"Log entries in session: {len(st.session_state.log_entries)}")

# Pane 2: Agent Recommendations
with col2:
    st.header("Agent Recommendations")
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["Incident Report", "Fleet Summary"])
    
    with tab1:
        incident_report, report_exists = read_incident_report()
        if report_exists and st.session_state.last_analysis_time:
            st.markdown(incident_report)
            st.caption(f"Last updated: {st.session_state.last_analysis_time.strftime('%H:%M:%S')}")
        else:
            st.markdown('<div style="color: #808080; padding: 20px; text-align: center;">Waiting for incident analysis...</div>', unsafe_allow_html=True)
    
    with tab2:
        fleet_summary, summary_exists = read_fleet_summary()
        if summary_exists and st.session_state.last_analysis_time:
            st.markdown(fleet_summary)
            st.caption(f"Last updated: {st.session_state.last_analysis_time.strftime('%H:%M:%S')}")
        else:
            st.markdown('<div style="color: #808080; padding: 20px; text-align: center;">Waiting for fleet analysis...</div>', unsafe_allow_html=True)

# Status bar at bottom
st.divider()
status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    if st.session_state.log_generator and st.session_state.log_generator.running:
        st.markdown('<p class="status-running"><strong>Log Generator:</strong> Running</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-stopped"><strong>Log Generator:</strong> Stopped</p>', unsafe_allow_html=True)

with status_col2:
    if st.session_state.crew_running:
        st.markdown('<p class="status-processing"><strong>Analysis:</strong> Running...</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-ready"><strong>Analysis:</strong> Ready</p>', unsafe_allow_html=True)

with status_col3:
    log_count = st.session_state.log_generator.get_log_count() if st.session_state.log_generator else 0
    st.markdown(f'<p style="color: #d4d4d4;"><strong>Log Entries:</strong> {log_count}</p>', unsafe_allow_html=True)

# Auto-refresh and auto-analyze logic
if st.session_state.log_generator and st.session_state.log_generator.running:
    # Check if new logs arrived
    log_file = Path("fleet_health.log")
    if log_file.exists():
        all_lines = log_file.read_text(encoding="utf-8").splitlines()
        current_log_count = len(all_lines)
        
        if current_log_count > st.session_state.last_log_count:
            # Auto-analyze if enabled
            if auto_analyze and not st.session_state.crew_running:
                time_since_last = (datetime.now() - st.session_state.last_analysis_time).total_seconds() if st.session_state.last_analysis_time else float('inf')
                if time_since_last >= analysis_interval:
                    # Run analysis in background thread
                    def run_analysis():
                        run_crew_analysis("fleet_health.log")
                    
                    thread = threading.Thread(target=run_analysis, daemon=True)
                    thread.start()
    
    # Auto-refresh every 2 seconds when generator is running
    time.sleep(2)
    st.rerun()
