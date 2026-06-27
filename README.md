# Autonomous Multi-Agent Orchestrator with Zero-Trust Sandbox

An enterprise-grade, state-driven multi-agent execution framework built in Python. This orchestrator utilizes an explicit Finite State Machine (FSM) to coordinate autonomous AI agents through iterative software engineering tasks, featuring runtime code execution inside an isolated, zero-trust container environment and an automated peer-review loop with human intervention fallback.

## 🏗️ Architecture Overview

The system is designed around a single source of truth (`AgentState`) passed deterministically between specialized nodes. Rather than relying on fragile, completely autonomous LLM loops, this framework enforces strict boundaries using an engineered pipeline:

[ Planning ] ──> [ Coding ] ──> [ Executing (Docker Sandbox) ]
▲                               │
│                               ▼
[ Human Override ] <── [ HITL ] <── [ Reviewing ]

1. **Planning Phase:** Initializes the target objective and configures system context.
2. **Coding Agent:** Generates executable logic addressing the target prompt or incorporating feedback from previous rejection loops.
3. **Sandbox Executor:** Spins up an ephemeral, lightweight, zero-trust Alpine Linux container via Docker to safely run generated code in complete isolation.
4. **Reviewer Agent:** Inspects stderr/stdout compilation logs and exit codes. Automatically approves code or provides structural feedback back to the Coder.
5. **Human-in-the-Loop (HITL):** A built-in circuit breaker that triggers after sequential failures, allowing an engineer to inject hints directly into shared system memory to break autonomous loops.

## ✨ Features

* **Deterministic State Machine:** Built around a formal `AgentState` paradigm preventing state drift or out-of-order execution.
* **Zero-Trust Ephemeral Sandbox:** Code execution occurs safely inside isolated Docker containers (`python:3.11-alpine`), protecting the host system from malicious or runaway logic.
* **Dynamic Terminal UI:** Powered by `Rich`, providing live status updating via multi-state loaders, clean visual panels, and real-time color-coded feedback.
* **Syntax Highlighted Outputs:** Final verified scripts are rendered using native terminal syntax highlighting (`Monokai` theme) with structural line numbering.

## 📂 Project Structure

```text
src/
├── agent_coder.py     # Generates targeted logic based on current state and history
├── agent_reviewer.py  # Evaluates execution logs and enforces compliance standards
├── executor.py        # Spawns ephemeral Docker runtime environments
├── state.py           # Core AgentState class definitions and schema management
├── orchestrator.py    # Master FSM execution loop and workflow coordination
└── main.py            # User-facing CLI entry point and interface layers

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* **Docker Desktop**: The Docker Engine **MUST** be actively running in the background before launching the orchestrator, as the system relies on it to spawn the zero-trust sandboxes.

### Installation

1. **Configure Docker:** Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/). 
   *Note for Windows Users: Ensure that "Use WSL 2 instead of Hyper-V" is checked during installation, and that WSL integration is enabled for your specific Linux distro in the settings.* **Start the Docker application and verify the engine is running.**

2. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git)
   cd YOUR_REPO_NAME



1. Set up the environment:

Create a virtual environment and install the required dependencies:
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install rich docker pydantic ollama

2.Verify Local LLM:

Ensure your local LLM inference engine (e.g., Ollama running mistral) is currently active and reachable by the backend modules.


Usage

Once Docker and your LLM are running, launch the orchestrator interface by executing the primary entry point:
python src/main.py

Provide your development objective when prompted, and observe the live multi-agent state transitions through your terminal UI.

