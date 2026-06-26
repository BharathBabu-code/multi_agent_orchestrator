import ollama
from pydantic import BaseModel, Field
from state import AgentState
import re

class CoderOutput(BaseModel):
    """The strict schema the LLM MUST adhere to when generating code."""
    thought_process: str = Field(
        ..., 
        description="A brief explanation of how you are solving the problem."
    )
    code_snippet: str = Field(
        ..., 
        description="The raw, executable Python 3 code. Do NOT include markdown formatting like ```python."
    )

def generate_code(state: AgentState) -> CoderOutput:
    """
    Takes the current state, feeds it to the LLM, and returns a validated CoderOutput object.
    """
    print(f"[*] Coder Agent: Analyzing task... (Iteration {state.iteration_count + 1})")
    
    #System instruction
    system_prompt = (
        "You are an elite Python backend developer. Your job is to write clean, secure, and executable code.\n"
        "You will be provided with a task, a history of past attempts, and the latest feedback.\n"
        "Pay close attention to the Execution History to avoid repeating mistakes or ignoring human hints.\n"
        "Respond ONLY with the required JSON structure."
    )
    
    #Context from the state
    user_context = f"Task: {state.task}\n"
    # LONG-TERM MEMORY: Inject the entire history log
    if state.history:
        user_context += "\n--- EXECUTION HISTORY ---\n"
        for i, entry in enumerate(state.history):
            user_context += f"Step {i + 1}: {entry}\n"
            
    # SHORT-TERM MEMORY: Inject the immediate feedback
    if state.reviewer_feedback:
        user_context += f"\n--- LATEST REVIEWER FEEDBACK ---\n{state.reviewer_feedback}\n" 
    try:
        response = ollama.chat(
            model='mistral',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_context}
            ],
            format=CoderOutput.model_json_schema()
        )
        
        parsed_output = CoderOutput.model_validate_json(response['message']['content'])
        raw_code = parsed_output.code_snippet.strip()
        cleaned_code = re.sub(r"^```(?:python)?\n|\n```$", "", raw_code)
        parsed_output.code_snippet = cleaned_code.strip()
        return parsed_output
        
    except Exception as e:
        print(f"[!] Coder Agent Error: {e}")
        # Returns a safe fallback if the connection fails
        return CoderOutput(
            thought_process="Error connecting to local LLM.",
            code_snippet="print('Error generation failed.')"
        )

if __name__ == "__main__":
    # Testing the Coder Agent with injected history
    dummy_state = AgentState(task="Write a function that returns the square root of a number.")
    dummy_state.history = ["Coder thought: I will use the math library.", "Reviewer rejected. Reason: Do not use the math library, write it from scratch.", "Human Intervention: Try using the Newton-Raphson method."]
    dummy_state.reviewer_feedback = "SyntaxError: invalid syntax on line 4"
    
    result = generate_code(dummy_state)
    print("\n--- CODER OUTPUT ---")
    print(f"Thoughts: {result.thought_process}")
    print(f"Code:\n{result.code_snippet}")