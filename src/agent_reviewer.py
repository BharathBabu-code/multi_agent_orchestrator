import ollama
from pydantic import BaseModel, Field
from state import AgentState

class ReviewerOutput(BaseModel):
    """The strict schema the Reviewer LLM MUST adhere to."""
    is_approved: bool = Field(
        ..., 
        description="Set to true ONLY if the execution output is exactly what was expected with no errors."
    )
    feedback: str = Field(
        ..., 
        description="If rejected, detail exactly why it failed and how the coder should fix it. If approved, output 'Pass'."
    )

def review_code(state: AgentState) -> ReviewerOutput:
    """
    Evaluates the code and the terminal execution logs to decide if the task is complete.
    """
    print("[*] Reviewer Agent: Evaluating execution logs...")
    
    system_prompt = (
        "You are an elite Quality Assurance AI. Your job is to verify if the execution output matches the expected result of the task.\n"
        "CRITICAL RULE 1: If the Execution History contains a 'Human Intervention', those human instructions completely OVERRIDE the original task requirements. You must evaluate the code based on the human's new rules.\n"
        "CRITICAL RULE 2: If the TERMINAL EXECUTION LOGS contain a 'CRASH LOG', a traceback, or any errors, you MUST reject the code (is_approved = False). NEVER approve code that crashes.\n"
        "Respond ONLY with the required JSON structure."
    )
    
    user_context = f"Original Task: {state.task}\n\n"
    
    # LONG-TERM MEMORY: Injects the history so the Reviewer sees human hints
    if state.history:
        user_context += "--- EXECUTION HISTORY & HUMAN OVERRIDES ---\n"
        for i, entry in enumerate(state.history):
            user_context += f"Step {i + 1}: {entry}\n"
            
    user_context += f"\n--- CODE TO REVIEW ---\n{state.current_code}\n\n"
    user_context += f"--- TERMINAL EXECUTION LOGS ---\n{state.execution_output}\n"
    
    try:
        response = ollama.chat(
            model='mistral',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_context}
            ],
            format=ReviewerOutput.model_json_schema()
        )
        
        parsed_output = ReviewerOutput.model_validate_json(response['message']['content'])
        return parsed_output
        
    except Exception as e:
        print(f"[!] Reviewer Agent Error: {e}")
        return ReviewerOutput(
            is_approved=False,
            feedback=f"System error during review process: {e}"
        )

if __name__ == "__main__":
    # Testing the Reviewer Agent
    dummy_state = AgentState(
        task="Write a script that prints 'Hello World'",
        current_code="prnt('Hello World')", # Intentional typo
        execution_output="NameError: name 'prnt' is not defined"
    )
    
    result = review_code(dummy_state)
    print("\n--- REVIEWER OUTPUT ---")
    print(f"Approved: {result.is_approved}")
    print(f"Feedback: {result.feedback}")