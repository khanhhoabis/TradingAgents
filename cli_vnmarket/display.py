import time
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.spinner import Spinner
from rich.live import Live
from pathlib import Path

console = Console()

def print_banner():
    """Print the welcome ASCII banner."""
    banner_path = Path(__file__).parent / "static" / "banner.txt"
    try:
        with open(banner_path, "r", encoding="utf-8") as f:
            banner_ascii = f.read()
    except FileNotFoundError:
        banner_ascii = "VN MARKET CLI"

    welcome_content = f"[bold cyan]{banner_ascii}[/bold cyan]\n"
    welcome_content += "[dim]Vietnam Stock Market Data Collection Framework[/dim]"

    welcome_box = Panel(
        welcome_content,
        border_style="cyan",
        padding=(1, 2),
        title="Welcome",
    )
    console.print(Align.center(welcome_box))
    console.print()

def display_mock_data(ticker: str, action: str, data: list):
    """Display the fetched mock data in a rich table."""
    table = Table(title=f"Results: {action} for {ticker}", header_style="bold magenta", expand=True)
    
    if not data:
        console.print("[yellow]No data returned.[/yellow]")
        return

    # Add columns based on the first item's keys
    for key in data[0].keys():
        table.add_column(key.capitalize(), style="cyan", justify="center")
        
    # Add rows
    for item in data:
        row = [str(val) for val in item.values()]
        table.add_row(*row)
        
    console.print(Panel(table, border_style="green"))
