# AiopsSre Crew

## Overview
This repository implements an **AIOps/SRE multi-agent system** using the **crewAI framework**. The system monitors fleet health logs, detects anomalies, and generates incident reports and fleet summaries.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```

### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/aiops_sre/config/agents.yaml` to define your agents
- Modify `src/aiops_sre/config/tasks.yaml` to define your tasks
- Modify `src/aiops_sre/crew.py` to add your own logic, tools and specific args
- Modify `src/aiops_sre/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the aiops_sre Crew, assembling the agents and assigning them tasks as defined in your configuration.

---

## Functional Components

### 1. **Crew Class** (`src/aiops_sre/crew.py`)
- **Purpose**: Main orchestrator that defines agents, tasks, and their relationships
- **Class**: `AiopsSreCrew` decorated with `@CrewBase`
- **Key Features**:
  - Loads agent configurations from `config/agents.yaml`
  - Loads task configurations from `config/tasks.yaml`
  - Defines agent methods using `@agent` decorator
  - Defines task methods using `@task` decorator
  - Assembles the Crew with `@crew` decorator

### 2. **Agents** (2 agents defined)
- **sre_agent**: 
  - Role: Senior Site Reliability Engineer
  - Tools: `tail_log` (custom tool for reading log files)
  - Purpose: Triage incidents from logs, classify severity, recommend remediation
  
- **fleet_health_analyst**:
  - Role: Fleet Health Analyst
  - Tools: None (relies on previous task output)
  - Purpose: Aggregate incidents and produce executive health summaries

### 3. **Tasks** (2 tasks defined)
- **log_triage_task**:
  - Assigned to: `sre_agent`
  - Purpose: Read logs, detect anomalies, generate incident report
  - Output: `incident_report.md`
  
- **fleet_summary_task**:
  - Assigned to: `fleet_health_analyst`
  - Purpose: Create fleet health summary from incident report
  - Output: `fleet_summary.md`

### 4. **Tools** (`src/aiops_sre/tools/`)
- **tail_log** (`log_tools.py`):
  - Function-based tool using `@tool` decorator
  - Reads last N lines from a log file
  - Used by `sre_agent`
  
- **MyCustomTool** (`custom_tool.py`):
  - Class-based tool template (not currently used)
  - Example implementation of `BaseTool`

### 5. **Configuration Files**
- **agents.yaml**: Defines agent roles, goals, and backstories
- **tasks.yaml**: Defines task descriptions, expected outputs, and agent assignments

### 6. **Entry Points** (`src/aiops_sre/main.py`)
- `run()`: Standard execution
- `train()`: Training mode with iterations
- `replay()`: Replay from a specific task
- `test()`: Test execution with evaluation
- `run_with_trigger()`: Execution with trigger payload

---

## Agent Initialization

### How Agents Are Initialized

1. **Declaration**: Agents are declared as methods in `AiopsSreCrew` class with `@agent` decorator:
   ```python
   @agent
   def sre_agent(self) -> Agent:
       return Agent(
           config=self.agents_config["sre_agent"],
           tools=[tail_log],
       )
   ```

2. **Configuration Loading**: 
   - The `@CrewBase` decorator automatically loads YAML configs
   - `agents_config` points to `config/agents.yaml`
   - Each agent's config is accessed via dictionary key (e.g., `"sre_agent"`)

3. **Tool Assignment**: 
   - Tools are passed directly to `Agent()` constructor
   - Only `sre_agent` has tools (`tail_log`)
   - `fleet_health_analyst` has no tools

4. **Instantiation**: 
   - Agents are instantiated when `crew()` method is called
   - `self.sre_agent()` and `self.fleet_health_analyst()` are invoked
   - Agents are passed to `Crew()` constructor

### Agent Responsibilities
- **sre_agent**: Executes `log_triage_task` using `tail_log` tool to read and analyze logs
- **fleet_health_analyst**: Executes `fleet_summary_task` by analyzing the output from previous task

---

## Task Initialization

### How Tasks Are Initialized

1. **Declaration**: Tasks are declared as methods with `@task` decorator:
   ```python
   @task
   def log_triage_task(self) -> Task:
       return Task(
           config=self.tasks_config["log_triage_task"],
       )
   ```

2. **Configuration Loading**:
   - `tasks_config` points to `config/tasks.yaml`
   - Task configs include: `description`, `expected_output`, `agent`, `output_file`

3. **Agent Assignment**:
   - **Critical**: Each task MUST have an `agent:` field in `tasks.yaml`
   - `log_triage_task` → `agent: sre_agent`
   - `fleet_summary_task` → `agent: fleet_health_analyst`

4. **Task Dependencies**:
   - Tasks are executed sequentially (`Process.sequential`)
   - `fleet_summary_task` depends on output from `log_triage_task`
   - Dependencies are implicit through task order in Crew

5. **Instantiation**:
   - Tasks are instantiated when `crew()` method is called
   - `self.log_triage_task()` and `self.fleet_summary_task()` are invoked
   - Tasks are passed to `Crew()` constructor

### Task Execution Model
- Tasks are **always executed by agents** - there is no standalone task execution
- Each task has exactly one assigned agent (via `agent:` field in YAML)
- Tasks can reference previous task outputs in their descriptions

---

## Can Tasks Exist Without Agents?

### Answer: **NO** (in this implementation)

**Evidence:**
1. **YAML Configuration Requirement**: Every task in `tasks.yaml` has an `agent:` field:
   ```yaml
   log_triage_task:
     agent: sre_agent  # Required field
   ```

2. **CrewAI Framework Design**: Tasks are designed to be executed by agents. The framework expects:
   - Tasks to have an assigned agent
   - Agents to execute tasks using their LLM capabilities and tools

3. **No Standalone Task Execution**: There's no mechanism in the codebase to:
   - Execute tasks without agents
   - Run tasks as background processes
   - Create async tasks that don't require agents

### Can There Be Async Tasks?

**Answer: NO** (currently not implemented)

**Evidence:**
1. **No Async Code**: Grep search found zero instances of `async`, `Async`, or `asyncio`
2. **Synchronous Execution**: All execution is synchronous:
   - `crew().kickoff()` is a blocking call
   - Tasks execute sequentially (`Process.sequential`)
   - No async/await patterns

3. **Framework Limitation**: While crewAI might support async in theory, this implementation is fully synchronous

**Note**: The framework could potentially support async tasks in the future, but:
- They would still require agents (agents execute tasks)
- The current codebase has no async infrastructure

---

## Information Flow: From User Call to Completion

### Flow Diagram

```
User Function Call (main.py)
    ↓
AiopsSreCrew().crew().kickoff(inputs={...})
    ↓
CrewAI Framework Initialization
    ↓
┌─────────────────────────────────────┐
│ 1. Crew Assembly                    │
│    - Instantiate agents             │
│    - Instantiate tasks              │
│    - Configure Process.sequential   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Task 1: log_triage_task          │
│    Agent: sre_agent                 │
│    ↓                                 │
│    a. Input interpolation           │
│       - {log_path} → "fleet_health.log" │
│    ↓                                 │
│    b. Agent receives task           │
│    ↓                                 │
│    c. Agent uses tail_log tool      │
│       - Reads last 20 lines         │
│    ↓                                 │
│    d. Agent analyzes logs           │
│       - Detects anomalies           │
│       - Classifies severity         │
│       - References playbooks.md     │
│    ↓                                 │
│    e. Agent generates output        │
│    ↓                                 │
│    f. Output saved to               │
│       incident_report.md            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. Task 2: fleet_summary_task       │
│    Agent: fleet_health_analyst      │
│    ↓                                 │
│    a. Agent receives task           │
│    ↓                                 │
│    b. Agent reads previous output   │
│       - incident_report.md          │
│    ↓                                 │
│    c. Agent analyzes incidents      │
│       - Counts affected hosts       │
│       - Determines systemic vs isolated │
│       - Assesses fleet status       │
│    ↓                                 │
│    d. Agent generates summary       │
│    ↓                                 │
│    e. Output saved to               │
│       fleet_summary.md              │
└─────────────────────────────────────┘
    ↓
Return Result to User
```

### Detailed Step-by-Step Flow

#### **Step 1: User Invocation**
```python
# main.py:run()
AiopsSreCrew().crew().kickoff(inputs={"log_path": "fleet_health.log"})
```

#### **Step 2: Crew Initialization**
1. `AiopsSreCrew()` instance created
2. `@CrewBase` decorator loads YAML configs:
   - `agents_config` → loads `config/agents.yaml`
   - `tasks_config` → loads `config/tasks.yaml`
3. `crew()` method called:
   - `self.sre_agent()` → Creates Agent with config + tools
   - `self.fleet_health_analyst()` → Creates Agent with config
   - `self.log_triage_task()` → Creates Task with config
   - `self.fleet_summary_task()` → Creates Task with config
4. `Crew()` object created with:
   - Agents list: `[sre_agent, fleet_health_analyst]`
   - Tasks list: `[log_triage_task, fleet_summary_task]`
   - Process: `Process.sequential`
   - Verbose: `True`

#### **Step 3: Task 1 Execution (log_triage_task)**
1. **Input Interpolation**: 
   - Task description contains `{log_path}`
   - Framework replaces with `"fleet_health.log"` from inputs

2. **Agent Assignment**:
   - Task config specifies `agent: sre_agent`
   - Framework assigns task to `sre_agent`

3. **Tool Execution**:
   - Agent calls `tail_log(path="fleet_health.log", n=20)`
   - Tool reads file and returns last 20 lines as string

4. **LLM Processing**:
   - Agent receives log content
   - Agent analyzes using thresholds (CPU > 80%, Memory > 90%, etc.)
   - Agent references `knowledge/playbooks.md` if needed
   - Agent generates markdown report

5. **Output Generation**:
   - Agent produces markdown formatted output
   - Framework saves to `incident_report.md` (per `output_file` in config)

#### **Step 4: Task 2 Execution (fleet_summary_task)**
1. **Input Access**:
   - Task description references "previous step" output
   - Agent can access `incident_report.md`

2. **Agent Assignment**:
   - Task config specifies `agent: fleet_health_analyst`
   - Framework assigns task to `fleet_health_analyst`

3. **LLM Processing**:
   - Agent reads `incident_report.md`
   - Agent aggregates incidents
   - Agent determines fleet status (GREEN/YELLOW/RED)
   - Agent generates executive summary

4. **Output Generation**:
   - Agent produces fleet health summary
   - Framework saves to `fleet_summary.md`

#### **Step 5: Completion**
- `kickoff()` returns result object
- Both output files are written to disk
- Execution completes synchronously

---

## Key Architectural Patterns

### 1. **Decorator-Based Configuration**
- `@CrewBase`: Enables YAML config loading
- `@agent`: Marks agent factory methods
- `@task`: Marks task factory methods
- `@crew`: Marks crew assembly method

### 2. **Configuration-Driven Design**
- Agents defined in YAML (roles, goals, backstories)
- Tasks defined in YAML (descriptions, outputs, agent assignments)
- Code provides structure, YAML provides content

### 3. **Sequential Processing**
- `Process.sequential` ensures tasks execute in order
- Task dependencies are implicit (later tasks reference earlier outputs)

### 4. **Tool Integration**
- Tools are Python functions/classes
- Decorated with `@tool` or extend `BaseTool`
- Assigned to agents, not tasks

### 5. **Input/Output Flow**
- Inputs passed via `kickoff(inputs={...})`
- Inputs interpolated into task descriptions (`{variable_name}`)
- Outputs written to files specified in `output_file` field

---

## Summary

**Agents**: 2 agents initialized via `@agent` decorator methods, configured from YAML, instantiated when Crew is created.

**Tasks**: 2 tasks initialized via `@task` decorator methods, configured from YAML, **always assigned to agents**, executed sequentially.

**Tasks Without Agents**: **Not possible** - every task requires an `agent:` field in YAML, and tasks are executed by agents.

**Async Tasks**: **Not implemented** - fully synchronous execution, no async/await patterns.

**Information Flow**: User calls function → Crew initialized → Agents instantiated → Tasks assigned → Sequential execution → Output files generated → Result returned.
