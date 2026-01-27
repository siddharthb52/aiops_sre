import time
from aiops_sre.crew import AiopsSreCrew  # or AiopsSre depending on your class name

LOG_PATH = "fleet_health.log"

def main():
    last_size = -1
    while True:
        try:
            size = __import__("os").path.getsize(LOG_PATH)
        except FileNotFoundError:
            size = 0

        # only run if the log changed
        if size != last_size:
            last_size = size
            AiopsSreCrew().crew().kickoff(inputs={"log_path": LOG_PATH})
            print("✅ Updated incident_report.md and fleet_summary.md")

        time.sleep(3)

if __name__ == "__main__":
    main()
