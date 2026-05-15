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

def display_data(ticker: str, action: str, data: str):
    """Display the fetched text data in a rich panel."""
    
    if not data or data.startswith("Error"):
        console.print(f"[yellow]Issue fetching data: {data}[/yellow]")
        return
        
    # We just wrap the text in a panel
    panel = Panel(
        data, 
        title=f"Results: {action} for {ticker}", 
        border_style="green",
        expand=True
    )
    console.print(panel)
