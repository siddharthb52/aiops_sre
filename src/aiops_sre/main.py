#!/usr/bin/env python
import sys
import warnings

from aiops_sre.crew import AiopsSreCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information.

# Potentially could change to a real log output e.g. smth like os.getenv("AIOPS_LOG_PATH", "fleet_health.log")
LOG_PATH = "fleet_health.log"


def run():
    """
    Run the crew.
    """
    inputs = {
        "log_path": LOG_PATH
    }

    try:
        AiopsSreCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    Usage: python -m aiops_sre.main train <n_iterations> <filename>
    """
    inputs = {
        "log_path": LOG_PATH
    }

    try:
        AiopsSreCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    Usage: python -m aiops_sre.main replay <task_id>
    """
    try:
        AiopsSreCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    Usage: python -m aiops_sre.main test <n_iterations> <eval_llm>
    """
    inputs = {
        "log_path": LOG_PATH
    }

    try:
        AiopsSreCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


def run_with_trigger():
    """
    Run the crew with trigger payload.
    Usage: python -m aiops_sre.main run_with_trigger '{"key":"value"}'
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "log_path": LOG_PATH,
    }

    try:
        result = AiopsSreCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
