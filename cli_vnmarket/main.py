import typer
from rich.live import Live
from rich.spinner import Spinner
import json
from pathlib import Path

from cli_vnmarket.display import print_banner, display_data, console
from cli_vnmarket.interactive import ask_ticker, ask_action
from cli_vnmarket.data_engine import fetch_data

app = typer.Typer(
    name="vnmarket",
    help="CLI for Vietnam Stock Market Data Collection",
    add_completion=False,
)

@app.command()
def start():
    """Start the interactive CLI session."""
    print_banner()
    
    ticker = ask_ticker()
    
    while True:
        action = ask_action()
        
        if action == "Exit":
            console.print("[dim]Exiting VN Market CLI... Goodbye![/dim]")
            break
            
        console.print()
        
        # Show spinner while fetching
        with Live(Spinner("dots", text=f"[cyan]Fetching {action} for {ticker}...[/cyan]"), refresh_per_second=10):
            data = fetch_data(ticker, action)
            
        # Display data
        display_data(ticker, action, data)
        
        # Optionally save to text/CSV
        output_dir = Path("outputs") / ticker
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine extension based on data content
        ext = ".csv" if "Historical" in action else ".txt"
        filename = action.lower().replace(" ", "_").replace("_(ohlcv)", "") + ext
        
        with open(output_dir / filename, "w", encoding="utf-8") as f:
            f.write(data)
            
        console.print(f"[dim]Data saved to {output_dir / filename}[/dim]\n")

if __name__ == "__main__":
    app()
