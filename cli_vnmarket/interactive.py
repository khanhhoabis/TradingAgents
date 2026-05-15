import questionary
from rich.console import Console
import typer

console = Console()

def ask_ticker() -> str:
    ticker = questionary.text(
        "Enter the exact ticker symbol to analyze (e.g., FPT, HPG, SSI):",
        validate=lambda text: len(text.strip()) > 0 and text.strip().isalnum() or "Please enter a valid ticker."
    ).ask()
    
    if not ticker:
        console.print("[red]No ticker symbol provided. Exiting...[/red]")
        raise typer.Exit(1)
        
    return ticker.strip().upper()

def ask_action() -> str:
    action = questionary.select(
        "Select the type of data you want to fetch:",
        choices=[
            "Historical Price (OHLCV)",
            "Financial Reports",
            "Company Profile",
            "Exit"
        ]
    ).ask()
    
    return action
