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
        "You are a strict Senior Quality Assurance Engineer. \n"
        "You will review a Python script and its terminal output (stdout/stderr).\n"
        "If there are any errors or the output does not satisfy the original task, reject it and provide actionable feedback.\n"
        "Respond ONLY with the required JSON structure."
    )
    
    user_context = (
        f"Original Task: {state.task}\n\n"
        f"Generated Code:\n{state.current_code}\n\n"
        f"Terminal Execution Output:\n{state.execution_output}"
    )
    
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
    # Test the Reviewer Agent
    dummy_state = AgentState(
        task="Write a script that prints 'Hello World'",
        current_code="prnt('Hello World')", # Intentional typo
        execution_output="NameError: name 'prnt' is not defined"
    )
    
    result = review_code(dummy_state)
    print("\n--- REVIEWER OUTPUT ---")
    print(f"Approved: {result.is_approved}")
    print(f"Feedback: {result.feedback}")