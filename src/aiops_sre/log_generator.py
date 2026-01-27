"""
Log Generator - Streams log entries from source file to fleet_health.log at configurable intervals.
"""
import time
import json
from pathlib import Path
from typing import Optional
import threading


class LogGenerator:
    """Generates logs by reading from a source file and appending to target log file."""
    
    def __init__(
        self,
        source_file: str = "logs_source.jsonl",
        target_file: str = "fleet_health.log",
        interval_seconds: float = 2.0,
        start_from_line: int = 0
    ):
        """
        Initialize log generator.
        
        Args:
            source_file: Path to source JSONL file with log entries
            target_file: Path to target log file to write to
            interval_seconds: Time between log entries (seconds)
            start_from_line: Line number to start from (for resuming)
        """
        self.source_file = Path(source_file)
        self.target_file = Path(target_file)
        self.interval_seconds = interval_seconds
        self.current_line = start_from_line
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
    def _read_source_lines(self) -> list[str]:
        """Read all lines from source file."""
        if not self.source_file.exists():
            return []
        try:
            return self.source_file.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            print(f"Error reading source file: {e}")
            return []
    
    def _write_log_entry(self, entry: str):
        """Append a single log entry to target file."""
        try:
            with open(self.target_file, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def _generator_loop(self):
        """Main loop that generates logs."""
        lines = self._read_source_lines()
        total_lines = len(lines)
        
        if total_lines == 0:
            print(f"No lines found in source file: {self.source_file}")
            return
        
        print(f"Log generator started: {total_lines} entries available")
        
        while self.running and self.current_line < total_lines:
            with self.lock:
                if self.current_line < total_lines:
                    entry = lines[self.current_line]
                    self._write_log_entry(entry)
                    self.current_line += 1
                    print(f"Generated log entry {self.current_line}/{total_lines}")
            
            # Sleep for interval, but check running flag periodically
            sleep_interval = 0.1
            slept = 0.0
            while self.running and slept < self.interval_seconds:
                time.sleep(sleep_interval)
                slept += sleep_interval
        
        if self.current_line >= total_lines:
            print(f"All log entries generated. Total: {total_lines}")
        else:
            print("Log generator stopped")
    
    def start(self):
        """Start the log generator in a background thread."""
        if self.running:
            print("Log generator already running")
            return
        
        # Clear target file if starting from beginning
        if self.current_line == 0 and self.target_file.exists():
            self.target_file.write_text("")
        
        self.running = True
        self.thread = threading.Thread(target=self._generator_loop, daemon=True)
        self.thread.start()
        print(f"Log generator started (interval: {self.interval_seconds}s)")
    
    def stop(self):
        """Stop the log generator."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        print("Log generator stopped")
    
    def reset(self):
        """Reset to beginning and clear target file."""
        with self.lock:
            self.current_line = 0
            if self.target_file.exists():
                self.target_file.write_text("")
        print("Log generator reset")
    
    def get_status(self) -> dict:
        """Get current status of log generator."""
        lines = self._read_source_lines()
        total_lines = len(lines)
        
        with self.lock:
            return {
                "running": self.running,
                "current_line": self.current_line,
                "total_lines": total_lines,
                "progress": f"{self.current_line}/{total_lines}" if total_lines > 0 else "0/0",
                "interval_seconds": self.interval_seconds
            }
    
    def get_log_count(self) -> int:
        """Get number of lines currently in target log file."""
        if not self.target_file.exists():
            return 0
        try:
            return len(self.target_file.read_text(encoding="utf-8").splitlines())
        except:
            return 0
