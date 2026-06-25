import time
from state import AgentState
from agent_coder import generate_code
from agent_reviewer import review_code
from executor import execute_code

def run_orchestrator(task_prompt: str) -> AgentState:
    """
    The Master Finite State Machine loop. 
    Routes the AgentState through the network of AI agents and the Docker sandbox.
    """
    print("=" * 60)
    print("INITIALIZING MULTI-AGENT ORCHESTRATOR")
    print("=" * 60)
    
    # Initialize the single source of truth
    state = AgentState(task=task_prompt, status="planning")
    
    # The Infinite Loop (protected by iteration limits later)
    while state.status not in ["completed", "failed", "hitl"]:
        
        print(f"\n[🔄 CURRENT STATE: {state.status.upper()} | Iteration: {state.iteration_count}]")
        
        if state.status == "planning":
            print("[*] Planning phase complete. Transitioning to Coder...")
            state.history.append("System initialized task.")
            state.status = "coding"
            
        elif state.status == "coding":
            # Pass state to Coder
            coder_output = generate_code(state)
            
            # Update state with new code
            state.current_code = coder_output.code_snippet
            state.history.append(f"Coder thought: {coder_output.thought_process}")
            
            print("[*] Code generated. Transitioning to Sandbox Executor...")
            state.status = "executing"
            
        elif state.status == "executing":
            # Pass state to Docker Sandbox
            state = execute_code(state)
            
            print("[*] Execution complete. Transitioning to Reviewer...")
            state.status = "reviewing"
            
        elif state.status == "reviewing":
            # Pass state to Reviewer
            reviewer_output = review_code(state)
            
            if reviewer_output.is_approved:
                print(f"[✅] Reviewer APPROVED the code!")
                state.history.append("Reviewer approved final execution.")
                state.status = "completed"
            else:
                print(f"[❌] Reviewer REJECTED the code. Feedback: {reviewer_output.feedback}")
                state.reviewer_feedback = reviewer_output.feedback
                state.history.append(f"Reviewer rejected. Reason: {reviewer_output.feedback}")
                
                # Increment the loop counter and send it back to the coder!
                state.iteration_count += 1
                state.status = "coding"
                
                # Basic circuit breaker (we upgrade this in Week 5)
                if state.iteration_count >= 5:
                    print("[!] MAXIMUM ITERATIONS REACHED. Forcing failure state.")
                    state.status = "failed"
                    
        # Small delay just so we can read the terminal output
        time.sleep(1)

    print("\n" + "=" * 60)
    if state.status == "completed":
        print("🎉 WORKFLOW COMPLETE 🎉")
        print("\n--- FINAL CODE ---")
        print(state.current_code)
    else:
        print("⚠️ WORKFLOW FAILED ⚠️")
        print("The agents could not solve the task within the iteration limit.")
    print("=" * 60)
    
    return state

if __name__ == "__main__":
    # The ultimate test: A logic puzzle that usually requires a rewrite
    test_task = "Write a Python script that prints numbers from 1 to 15. But for multiples of 3, print 'Fizz', for multiples of 5, print 'Buzz', and for multiples of both, print 'FizzBuzz'."
    
    final_state = run_orchestrator(test_task)