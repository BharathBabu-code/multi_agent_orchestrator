from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError

class AgentState(BaseModel):
    """
    The immutable single source of truth for the Orchestrator FSM.
    Tracks the objective, code iterations, sandbox logs, and system status.
    """
    # FORCES CONTINUOUS VALIDATION
    model_config = {"validate_assignment": True}

    # Core Objectives & History
    task: str = Field(
        ..., 
        description="The original user objective or requirement script to generate."
    )
    history: List[str] = Field(
        default_factory=list, 
        description="Chronological log of agent reasoning, modifications, and human insights."
    )
    
    # State Artifacts
    current_code: str = Field(
        default="", 
        description="The latest iteration of the generated Python script."
    )
    execution_output: str = Field(
        default="", 
        description="The raw stdout/stderr output captured from the ephemeral Docker sandbox container."
    )
    reviewer_feedback: str = Field(
        default="", 
        description="Explicit structured critique from the Reviewer Agent if the code fails validation."
    )
    
    # Flow Control & Safety Circuit Breakers
    status: Literal["planning", "coding", "executing", "reviewing", "hitl", "completed", "failed"] = Field(
        default="planning", 
        description="The current active execution node in the Finite State Machine graph."
    )
    iteration_count: int = Field(
        default=0, 
        description="The number of recursive loops between Coder and Executor. Hard-capped to prevent infinite run costs."
    )

if __name__ == "__main__":
    # Initialize a valid state
    try:
        initial_state = AgentState(task="Write a basic calculator script")
        print("State initialized successfully.")
        
        # Test intentional type validation failure
        print("[*] Testing safety validation...")
        initial_state.status = "invalid_node_name"
        
    except ValidationError as e:
        print("Pydantic successfully intercepted an invalid state transition!")