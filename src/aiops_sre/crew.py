from __future__ import annotations

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from .tools.log_tools import tail_log


@CrewBase
class AiopsSreCrew:
    """AIOps/SRE PoC crew that reads logs and outputs incidents + fleet summary."""

    # These paths match your scaffold layout
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def sre_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["sre_agent"],
            tools=[tail_log],
        )

    @agent
    def fleet_health_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["fleet_health_analyst"],
        )

    @task
    def log_triage_task(self) -> Task:
        return Task(
            config=self.tasks_config["log_triage_task"],
        )

    @task
    def fleet_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config["fleet_summary_task"],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.sre_agent(), self.fleet_health_analyst()],
            tasks=[self.log_triage_task(), self.fleet_summary_task()],
            process=Process.sequential,
            verbose=True,
        )
