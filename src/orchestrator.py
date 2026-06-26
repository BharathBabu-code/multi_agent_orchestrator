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
    while state.status not in ["completed", "failed"]:
        
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
                # THE CIRCUIT BREAKER
                if state.iteration_count >= 2:
                    print("\n[!] MAXIMUM ITERATIONS REACHED. Agents are stuck.")
                    state.status = "hitl"
                else:
                    state.status = "coding"
        
        #HUMAN-IN-THE-LOOP (HITL) NODE
        elif state.status == "hitl":
            print("\n" + "=" * 60)
            print(" HUMAN INTERVENTION REQUIRED ")
            print("The agents have failed 5 times in a row. They need your expertise.")
            print(f"Latest Reviewer Feedback: {state.reviewer_feedback}")
            print("=" * 60)
            
            human_hint = input("\n[?] Enter a hint for the Coder (or type 'exit' to abort): ").strip()
            
            if human_hint.lower() == 'exit':
                print("[*] Aborting workflow by human command.")
                state.status = "failed"
            else:
                # Inject the human hint into the system memory
                state.reviewer_feedback = f"HUMAN OVERRIDE HINT: {human_hint} (Previous error: {state.reviewer_feedback})"
                state.history.append(f"Human Intervention: {human_hint}")
                
                # Reset the counter and send them back to work!
                state.iteration_count = 0 
                state.status = "coding"
                print("\n[*] Hint injected into shared memory. Resuming autonomous loop...")          
        
        # Small delay just so we can read the terminal output
        time.sleep(1)

    print("\n" + "=" * 60)
    if state.status == "completed":
        print("🎉 WORKFLOW COMPLETE 🎉")
        print("\n--- FINAL CODE ---")
        print(state.current_code)
    else:
        print("⚠️ WORKFLOW FAILED OR ABORTED ⚠️")
    print("=" * 60)
    
    return state

if __name__ == "__main__":
    # This will fail because 'pandas' is not installed in the basic python:3.11-alpine Docker container!
    test_task = "Write a script that imports pandas, creates a basic dataframe, and prints it."
    final_state = run_orchestrator(test_task)