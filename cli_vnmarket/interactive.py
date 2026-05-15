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
    """Ask the user what action they want to perform."""
    action = questionary.select(
        "What do you want to do?",
        choices=[
            "Historical Price (OHLCV)",
            "Company Profile",
            "Balance Sheet",
            "Income Statement",
            "Cash Flow",
            "Exit"
        ],
        style=custom_style
    ).ask()
    
    return action

def ask_frequency() -> str:
    """Ask the user for financial report frequency."""
    freq = questionary.select(
        "Select report frequency:",
        choices=[
            "Quarterly",
            "Annual"
        ],
        style=custom_style
    ).ask()
    
    return freq
