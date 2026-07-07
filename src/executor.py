import docker
import textwrap
from state import AgentState

def execute_code(state: AgentState) -> AgentState:
    """
    Takes the generated code from the state, runs it inside an isolated, 
    ephemeral Docker container, and captures the terminal output.
    """
    print(f"[*] Executor Node: Spinning up Zero-Trust Sandbox...")
    
    # Initializing the Docker client
    try:
        client = docker.from_env()
    except docker.errors.DockerException:
        print("[!] ERROR: Cannot connect to Docker. Is Docker running?")
        state.execution_output = "SYSTEM_ERROR: Docker daemon is not running."
        return state

    # We use a highly stripped down version of Linux (Alpine) for maximum speed and security
    image = "python:3.11-alpine"
    
    # We must properly escape the code so it can be passed as a single string command to the container
    safe_code = state.current_code
    
    try:
        #Imp Notes:
        # Run the container
        # - remove=True means the container deletes itself the millisecond it finishes
        # - mem_limit restricts the AI from crashing our RAM
        # - network_disabled=True means the AI cannot access the internet to download malware
        print("    -> Running code inside isolated alpine container...")
        
        container_output = client.containers.run(
            image=image,
            command=["python", "-c", safe_code],
            remove=True,                # Instantly destroy after running
            network_disabled=True,      # No internet access
            mem_limit="128m",           # Prevent memory bombs
            environment={"PYTHONUNBUFFERED": "1"} # Force Python to print logs instantly
        )
        
        result_logs = container_output.decode('utf-8').strip()
        
        if not result_logs:
            result_logs = "[Execution successful, but no output was printed to the terminal]"
            
        state.execution_output = result_logs
        print("    -> Execution complete. Output captured.")
        
    except docker.errors.ContainerError as e:
        #Imp notes
        # If the python code crashes (SyntaxError, TypeError, etc.), it throws a ContainerError.
        # We capture the stderr traceback here to feed back to the Reviewer.
        print("    -> [!] Code crashed during execution.")
        error_logs = e.stderr.decode('utf-8').strip() if e.stderr else str(e)
        state.execution_output = f"CRASH LOG:\n{error_logs}"
        
    except Exception as e:
        # Catch any other system-level errors
        state.execution_output = f"SYSTEM_ERROR: {str(e)}"
        
    return state

if __name__ == "__main__":
    # --- TEST 1: Safe Code ---
    print("\n--- RUNNING TEST 1 (Safe Code) ---")
    safe_state = AgentState(
        task="Test basic math",
        current_code="print('Hello from inside the secure container!')\nprint(10 * 5)"
    )
    safe_result = execute_code(safe_state)
    print(f"\nCaptured Output:\n{safe_result.execution_output}")
    
    # --- TEST 2: Malicious/Crashing Code ---
    print("\n--- RUNNING TEST 2 (Crashing Code) ---")
    crash_state = AgentState(
        task="Test error handling",
        current_code="import math\nprint(math.sqrt(-1))" # Math domain error
    )
    crash_result = execute_code(crash_state)
    print(f"\nCaptured Output:\n{crash_result.execution_output}")