import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.syntax import Syntax

from orchestrator import run_orchestrator

console = Console()

def main():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Native Multi-Agent Orchestrator[/bold cyan]\n"
        "[dim]Zero-Trust Execution | Constrained Decoding | HITL[/dim]", 
        border_style="cyan"
    ))
    
    task = Prompt.ask("\n[bold green]What would you like the agents to build?[/bold green]")
    
    if not task.strip():
        console.print("[red]Task cannot be empty. Exiting.[/red]")
        sys.exit(1)
        
    final_state = run_orchestrator(task)
    
    console.print("\n")
    if final_state.status == "completed":
        console.print(Panel("[bold green]! WORKFLOW COMPLETE ![/bold green]", border_style="green"))
        
        # Display the code with Python syntax highlighting
        syntax = Syntax(final_state.current_code, "python", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="[bold cyan]Final Generated Script[/bold cyan]", border_style="cyan"))
        
    else:
        console.print(Panel("[bold red] !!WORKFLOW ABORTED OR FAILED!![/bold red]", border_style="red"))
        
    console.print("\n[dim]Shutting down system...[/dim]")

if __name__ == "__main__":
    main()