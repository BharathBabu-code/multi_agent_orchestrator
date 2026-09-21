# Autonomous Multi-Agent Orchestrator with Zero-Trust Sandbox

A **state-driven multi-agent software engineering framework** that coordinates AI agents through planning, code generation, sandboxed execution, automated review, and iterative correction.

Built with **Python, Docker, Ollama, Pydantic, and Rich**, the system uses an explicit **Finite State Machine (FSM)** as the central workflow controller rather than relying on an unconstrained autonomous agent loop.

Generated code is executed inside an **ephemeral, resource-limited Docker sandbox**, while a reviewer agent analyzes execution results and feeds structured feedback back to the coding agent. A **Human-in-the-Loop (HITL) circuit breaker** provides a controlled intervention point when autonomous attempts repeatedly fail.

> **Core idea:** Give autonomous agents freedom to solve a task, while enforcing deterministic state transitions, isolated execution, structured communication, and human intervention boundaries.

---

## Overview

Autonomous coding agents can generate useful software, but completely open-ended agent loops introduce several engineering problems:

* Generated code may fail at runtime.
* Agents may repeatedly make the same mistake.
* Model outputs may not follow the expected structure.
* Executing generated code directly on the host is unsafe.
* Autonomous loops can continue indefinitely without intervention.

This project addresses these problems by placing the agents inside an explicitly controlled execution pipeline:

```text
User Objective
      ↓
   Planning
      ↓
    Coding
      ↓
Docker Sandbox Execution
      ↓
   Review
      │
      ├── Approved ──────────→ Complete
      │
      └── Rejected
             ↓
       Feedback → Coding
             │
             ↓
       Repeated Failures
             ↓
       Human Intervention
```

The workflow is coordinated through a shared `AgentState` object, providing a **single source of truth** for the entire execution cycle.

---

## Architecture

The orchestrator follows a deterministic state-machine architecture.

```text
                       ┌─────────────────┐
                       │  User Objective │
                       └────────┬────────┘
                                ↓
                       ┌─────────────────┐
                       │     Planning    │
                       └────────┬────────┘
                                ↓
                       ┌─────────────────┐
                  ┌───→│      Coding     │
                  │    └────────┬────────┘
                  │             ↓
                  │    ┌─────────────────┐
                  │    │ Docker Sandbox  │
                  │    │   Execution     │
                  │    └────────┬────────┘
                  │             ↓
                  │    ┌─────────────────┐
                  │    │     Review      │
                  │    └────────┬────────┘
                  │             │
                  │       ┌─────┴─────┐
                  │       │           │
                  │    Approved    Rejected
                  │       │           │
                  │       ↓           ↓
                  │    Complete    Feedback
                  │                   │
                  │                   └─────────┐
                  │                             ↓
                  │                           Coding
                  │
                  │
                  └──── Repeated Failures
                              ↓
                       ┌─────────────────┐
                       │      HITL       │
                       │ Human Override  │
                       └────────┬────────┘
                                ↓
                              Coding
```

### 1. Planning

The system initializes the objective and establishes the context required by downstream agents.

The resulting information is stored in the shared `AgentState`.

---

### 2. Coding Agent

The coding agent generates executable code based on:

* The original objective
* Current system state
* Previous execution results
* Reviewer feedback
* Human-provided hints, when available

If a previous attempt fails, the coding agent receives structured feedback and generates a revised implementation.

---

### 3. Zero-Trust Sandbox

Generated code is **never executed directly on the host system**.

Instead, the executor creates an ephemeral Docker environment based on:

```text
python:3.11-alpine
```

The sandbox is configured with resource restrictions, including a **128 MB memory limit** in the current implementation.

```text
Generated Code
      ↓
Ephemeral Docker Container
      ↓
Restricted Execution
      ↓
stdout / stderr / exit code
      ↓
Reviewer
```

After execution, the environment can be discarded, preventing generated code from becoming a persistent part of the host environment.

> **Important:** Container isolation is a security boundary, but Docker containers should not be treated as an absolute security guarantee against all possible container-escape or kernel-level attacks.

---

### 4. Reviewer Agent

The reviewer analyzes the execution results, including:

* Exit codes
* `stdout`
* `stderr`
* Runtime failures
* Compilation/syntax errors
* Dependency-related failures

The reviewer can either:

**Approve**

```text
Execution successful
        ↓
Workflow Complete
```

or:

**Reject**

```text
Execution failure
        ↓
Structured Feedback
        ↓
Coding Agent
        ↓
New Attempt
```

This creates a self-correcting development loop.

---

### 5. Human-in-the-Loop Circuit Breaker

Autonomous systems can become trapped in repetitive failure cycles.

To prevent this, the orchestrator includes a **HITL circuit breaker**.

After sequential failed attempts, the system pauses autonomous execution and allows a human to provide additional guidance.

```text
Attempt 1 → Failure
Attempt 2 → Failure
Attempt 3 → Failure
                ↓
         HITL Intervention
                ↓
        Human provides hint
                ↓
         Agent resumes
```

This preserves autonomous execution while maintaining a clear human control boundary.

---

## Key Features

### 🤖 Self-Healing Agent Loop

The orchestrator automatically feeds execution failures back into the coding workflow.

Instead of:

```text
Generate → Execute → Fail → Stop
```

the system implements:

```text
Generate
   ↓
Execute
   ↓
Review
   ↓
Failure?
   ↓
Feedback
   ↓
Regenerate
   ↓
Execute Again
```

This allows the system to recover from issues such as syntax errors, runtime exceptions, and missing dependencies.

---

### 🔄 Deterministic Finite State Machine

The workflow is controlled by explicit states rather than an unconstrained LLM-driven loop.

The shared `AgentState` maintains the information required to coordinate agents and prevents unexpected state transitions.

This separates:

**AI reasoning**

from

**workflow control**

so that the LLM does not independently decide the overall execution flow.

---

### 🔒 Zero-Trust Code Execution

Generated code is treated as untrusted.

The execution layer uses ephemeral Docker containers rather than running generated scripts directly on the host.

Current sandbox configuration includes:

* Alpine Linux base image
* Python 3.11 runtime
* Ephemeral containers
* 128 MB memory limit
* Captured `stdout`
* Captured `stderr`
* Exit-code inspection

---

### 📐 Structured Agent Communication

Agent outputs are validated using **Pydantic schemas**.

Instead of relying on arbitrary text responses:

```text
LLM
 ↓
Structured Output
 ↓
Pydantic Validation
 ↓
AgentState
```

Malformed or unexpected outputs can therefore be rejected before they propagate through the workflow.

---

### 🚨 Controlled Failure Handling

The orchestrator uses structured exception handling around agent execution, Docker operations, parsing, and workflow transitions.

Combined with the HITL circuit breaker, this prevents uncontrolled failure loops.

---

### 🖥️ Interactive Terminal UI

The CLI uses **Rich** to provide:

* Live state transitions
* Agent status updates
* Execution feedback
* Reviewer results
* Formatted error messages
* Syntax-highlighted generated code
* Line-numbered final output

This makes the internal multi-agent workflow observable directly from the terminal.

---

## Agent Communication

The system uses a shared state object rather than passing loosely structured text between agents.

Conceptually:

```text
                 ┌──────────────────┐
                 │    AgentState    │
                 ├──────────────────┤
                 │ objective        │
                 │ generated_code   │
                 │ execution_result │
                 │ reviewer_feedback│
                 │ attempt_count    │
                 │ current_state    │
                 └────────┬─────────┘
                          │
             ┌────────────┼────────────┐
             ↓            ↓            ↓
          Coder        Executor      Reviewer
```

Pydantic validation ensures that state and agent outputs conform to the expected structure.

---

## Project Structure

```text
multi-agent-orchestrator/
│
├── src/
│   ├── agent_coder.py      # Generates and revises code
│   ├── agent_reviewer.py   # Reviews execution results
│   ├── executor.py         # Creates and manages Docker sandboxes
│   ├── state.py            # AgentState definitions and validation
│   ├── orchestrator.py     # FSM and workflow coordination
│   └── main.py             # CLI entry point
│
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Component   | Technology           | Purpose                      |
| ----------- | -------------------- | ---------------------------- |
| Language    | Python               | Core application             |
| Agent Model | Mistral              | Code generation and review   |
| LLM Runtime | Ollama               | Local model inference        |
| Workflow    | Finite State Machine | Deterministic orchestration  |
| Validation  | Pydantic             | Structured state and outputs |
| Execution   | Docker               | Isolated code execution      |
| Sandbox     | Python 3.11 Alpine   | Lightweight runtime          |
| Terminal UI | Rich                 | Interactive CLI              |
| Environment | Linux / WSL          | Development and execution    |

---

## Getting Started

### Prerequisites

Before running the project, make sure you have:

* Python 3.10+
* Docker Desktop / Docker Engine
* Ollama
* Mistral model
* Git

Docker must be running because the orchestrator creates containers dynamically during execution.

---

## Installation

### 1. Clone the repository



### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Linux / WSL**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Or install the primary dependencies directly:

```bash
pip install rich docker pydantic ollama
```

---

## Configure Ollama

Install [Ollama](https://ollama.com/) and pull the Mistral model:

```bash
ollama pull mistral
```

Verify that Ollama is available before starting the orchestrator.

---

## Verify Docker

Make sure Docker is running:

```bash
docker --version
```

You can also verify that the Docker daemon is reachable:

```bash
docker ps
```

If using Windows + WSL, ensure Docker Desktop's **WSL integration** is enabled for the Linux distribution you are using.

---

## Usage

Start the orchestrator:

```bash
python src/main.py
```

You will be prompted to provide a development objective.

For example:

```text
Build a Python program that analyzes a list of numbers
and returns the minimum, maximum, and average.
```

The orchestrator then executes the workflow:

```text
Planning
   ↓
Code Generation
   ↓
Docker Execution
   ↓
Review
   ↓
┌───────────────┐
│   Successful? │
└───────┬───────┘
        │
    Yes │ No
        │
        ↓       ↓
     Finish   Feedback
                  │
                  ↓
                Coding
```

The Rich terminal interface displays the state transitions and execution results while the workflow runs.

---

## Self-Healing Example

Suppose the coding agent generates code containing a missing dependency.

The workflow can identify the failure through the sandbox execution result:

```text
Coding Agent
     ↓
Generated Code
     ↓
Docker Execution
     ↓
ModuleNotFoundError
     ↓
Reviewer Agent
     ↓
"Required dependency is missing."
     ↓
Coding Agent
     ↓
Revised Implementation
     ↓
Docker Execution
     ↓
Success
```

The important distinction is that the reviewer does not directly modify the code. Instead, it provides structured feedback that is incorporated into the next coding attempt.

---

## Evaluation

The current implementation was evaluated on a set of coding tasks involving generated code execution and iterative correction.

### Observed Results

| Metric                       | Observed Result |
| ---------------------------- | --------------: |
| Task resolution success rate |         **80%** |
| Average task resolution time |  **70 seconds** |
| Sandbox memory limit         |      **128 MB** |

The **80% success rate** and **70-second average resolution time** reflect the project's evaluation runs and local execution environment. They should not be interpreted as universal performance guarantees across arbitrary coding tasks, models, or hardware.

---

## Security Model

The project uses multiple layers to reduce the risk associated with autonomous code generation.

```text
                 AI-Generated Code
                         │
                         ▼
                ┌─────────────────┐
                │ Docker Sandbox  │
                │                 │
                │ 128 MB Memory   │
                │ Alpine Linux    │
                └────────┬────────┘
                         │
                         ▼
                  Execution Result
                         │
                         ▼
                    AI Reviewer
                         │
              ┌──────────┴──────────┐
              │                     │
           Approve                Reject
              │                     │
              ▼                     ▼
           Complete             Feedback
                                    │
                                    ▼
                                  Coder
```

The security model is based on several principles:

### Untrusted Code

Generated code is assumed to be potentially unsafe and is therefore executed inside a separate container.

### Resource Limiting

The current executor applies a **128 MB memory limit** to reduce the impact of memory-intensive generated programs.

### Ephemeral Execution

Containers are created for individual execution tasks rather than serving as persistent execution environments.

### Controlled Autonomy

The FSM controls the workflow rather than allowing the LLM to arbitrarily determine the application's next state.

### Human Override

The HITL circuit breaker provides a mechanism for human intervention when autonomous recovery is unsuccessful.

---

## Why an FSM?

A completely autonomous agent loop might look like:

```text
LLM → Tool → LLM → Tool → LLM → ...
```

The problem is that the workflow itself becomes dependent on model decisions.

This project instead separates **reasoning from orchestration**:

```text
                ┌──────────────────┐
                │       FSM        │
                │ Workflow Control │
                └────────┬─────────┘
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
        Coder         Executor       Reviewer
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                    AgentState
```

The LLM handles tasks such as code generation and review, while the FSM determines **when and why each component runs**.

This makes the overall system easier to reason about, debug, and extend.

---

## Limitations

This project is a research/engineering prototype rather than a production-grade autonomous software development platform.

Current limitations include:

* The quality of generated code depends on the underlying LLM.
* Reviewer agents can incorrectly approve or reject generated code.
* Docker isolation is not an absolute security guarantee.
* The current sandbox is primarily designed for Python execution.
* Network restrictions and filesystem policies may require additional hardening for hostile workloads.
* The evaluation dataset is limited and may not represent all possible coding tasks.
* Local LLM inference performance depends heavily on available hardware.
* The current HITL policy is based on sequential failure handling rather than a learned intervention strategy.

---

## Future Improvements

Potential extensions include:

* [ ] Add stronger Docker security profiles
* [ ] Disable or restrict container networking
* [ ] Add CPU and execution-time limits
* [ ] Implement filesystem isolation policies
* [ ] Support multiple programming languages
* [ ] Add persistent task and execution history
* [ ] Add automated test generation
* [ ] Introduce dedicated testing agents
* [ ] Add static analysis before execution
* [ ] Add security scanning for generated dependencies
* [ ] Support configurable FSM workflows
* [ ] Add a web-based monitoring dashboard
* [ ] Benchmark multiple local and hosted LLMs
* [ ] Expand evaluation across larger coding-task datasets

---

## What This Project Demonstrates

This project demonstrates practical implementation of:

* Multi-agent system architecture
* Finite State Machines for AI orchestration
* Autonomous code generation
* Self-healing agent workflows
* Human-in-the-loop AI systems
* Docker-based sandboxing
* Zero-trust execution concepts
* Local LLM inference
* Pydantic schema validation
* Structured agent communication
* Runtime error recovery
* Resource-constrained execution
* Interactive CLI development

---

## License

This project is intended for educational, research, and software-engineering experimentation purposes.

