import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from state import AgentState
from agent_coder import generate_code
from agent_reviewer import review_code
from executor import execute_code

console = Console()

def run_orchestrator(task_prompt: str) -> AgentState:
    console.clear()
    console.print(Panel.fit("[bold cyan] INITIALIZING MULTI-AGENT ORCHESTRATOR[/bold cyan]", border_style="cyan"))
    
    state = AgentState(task=task_prompt, status="planning")
    
    # We wrap the main loop in a dynamic loading spinner
    with console.status("[bold green]System initializing...[/bold green]", spinner="dots4") as status_ui:
        
        while state.status not in ["completed", "failed"]:
            
            status_ui.update(f"[bold magenta]🔄 STATE: {state.status.upper()} | Iteration: {state.iteration_count}[/bold magenta]")
            time.sleep(1) # Brief pause for visual pacing
            
            if state.status == "planning":
                state.history.append("System initialized task.")
                state.status = "coding"
                
            elif state.status == "coding":
                status_ui.update(f"[bold yellow]⚙️  Coder Agent is writing logic... (Iteration {state.iteration_count})[/bold yellow]")
                coder_output = generate_code(state)
                state.current_code = coder_output.code_snippet
                state.history.append(f"Coder thought: {coder_output.thought_process}")
                state.status = "executing"
                
            elif state.status == "executing":
                status_ui.update("[bold blue]⚡ Spinning up Zero-Trust Docker Sandbox...[/bold blue]")
                state = execute_code(state)
                state.status = "reviewing"
                
            elif state.status == "reviewing":
                status_ui.update("[bold red]🔍 Reviewer Agent is analyzing execution logs...[/bold red]")
                reviewer_output = review_code(state)
                
                if reviewer_output.is_approved:
                    console.print("[bold green]✅ Reviewer APPROVED the code![/bold green]")
                    state.history.append("Reviewer approved final execution.")
                    state.status = "completed"
                else:
                    console.print(f"[bold red]❌ Reviewer REJECTED the code.[/bold red] [dim]Reason: {reviewer_output.feedback}[/dim]")
                    state.reviewer_feedback = reviewer_output.feedback
                    state.history.append(f"Reviewer rejected. Reason: {reviewer_output.feedback}")
                    state.iteration_count += 1
                    
                    if state.iteration_count >= 2:
                        console.print("[bold red blink]⚠️ MAXIMUM ITERATIONS REACHED.[/bold red blink]")
                        state.status = "hitl"
                    else:
                        state.status = "coding"
                        
            elif state.status == "hitl":
                # Pause the spinner to ask the human
                status_ui.stop() 
                
                console.print("\n")
                console.print(Panel("[bold red]🚨 HUMAN INTERVENTION REQUIRED 🚨[/bold red]\nThe agents are stuck in a loop. They need your architectural guidance.", border_style="red"))
                console.print(f"[yellow]Reviewer Feedback:[/yellow] {state.reviewer_feedback}")
                
                human_hint = Prompt.ask("\n[bold cyan][?] Enter a hint for the Coder (or type 'exit')[/bold cyan]")
                
                if human_hint.lower() == 'exit':
                    state.status = "failed"
                else:
                    state.reviewer_feedback = f"HUMAN OVERRIDE HINT: {human_hint} (Previous error: {state.reviewer_feedback})"
                    state.history.append(f"Human Intervention: {human_hint}")
                    state.iteration_count = 0 
                    state.status = "coding"
                    console.print("[bold green][*] Hint injected into memory. Resuming autonomous loop...[/bold green]")
                    
                # Restart the spinner
                status_ui.start() 

    return state