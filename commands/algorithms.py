"""
Algorithms command - View available attack algorithms with consistent verbs
"""

import sys
import argparse
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.json import JSON
import json
from utils import (
    APIClient, create_table, console, print_success, print_error,
    print_warning, print_info, print_panel, print_json, select_algorithm
)

def print_algorithms_help():
    """Print algorithms command help using Rich"""
    console.print(Panel.fit(
        "[bold red]Algorithms Command[/bold red] - View available attack algorithms",
        title="Algorithm Management",
        border_style="red"
    ))
    
    console.print("\n[bold]Usage:[/bold]")
    console.print("  ga-red algorithms [red]<action>[/red] [dim][options][/dim]\n")
    
    # Create actions table
    table = Table(title="Available Actions", show_header=True, header_style="bold red")
    table.add_column("Action", style="red", no_wrap=True)
    table.add_column("Description", style="white")
    
    table.add_row("list", "List available algorithms")
    table.add_row("show [name]", "Show algorithm details with params (interactive if no name)")
    
    console.print(table)
    
    console.print("\n[dim]For help on a specific action:[/dim]")
    console.print("  ga-red algorithms [red]<action>[/red] --help")
    console.print()

def add_parser(subparsers):
    """Add algorithms command parser"""
    parser = subparsers.add_parser(
        'algorithms',
        help='View available attack algorithms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='View and explore available attack algorithms',
        add_help=False
    )
    
    # Check if user is asking for help at algorithms level
    if len(sys.argv) >= 3 and sys.argv[1] == 'algorithms' and sys.argv[2] in ['--help', '-h']:
        print_algorithms_help()
        sys.exit(0)
    
    # Add help argument
    parser.add_argument('--help', '-h', action='store_true', help='Show help message')
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available algorithms')
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Show command (replaces get)
    show_parser = subparsers.add_parser('show', help='Show algorithm details')
    show_parser.add_argument('algorithm_name', nargs='?', help='Algorithm name (interactive if not provided)')
    show_parser.add_argument('--json', action='store_true', help='Output as JSON')

def execute(args):
    """Execute algorithms command"""
    if hasattr(args, 'help') and args.help:
        print_algorithms_help()
        return
        
    client = APIClient()
    
    if not args.action:
        print_algorithms_help()
        return
    
    if args.action == 'list':
        list_algorithms(client, args)
    elif args.action == 'show':
        show_algorithm(client, args)

def list_algorithms(client: APIClient, args):
    """List all available algorithms"""
    with console.status("[red]Fetching algorithms...[/red]"):
        response = client.get("/algorithms")
    
    if not response:
        return
    
    # New API returns a plain list
    algorithms = response if isinstance(response, list) else response.get('algorithms', [])
    
    if not algorithms:
        print_warning("No algorithms found")
        return
    
    if hasattr(args, 'json') and args.json:
        print_json(algorithms, title="Algorithms")
        return
    
    # Create table
    headers = ["Name", "Description", "Type"]
    rows = []
    
    for algo in algorithms:
        desc = algo.get('description', 'N/A')
        desc_display = desc[:60] + "..." if len(desc) > 60 else desc
        
        rows.append([
            algo.get('name', 'N/A'),
            desc_display,
            (algo.get('type') or 'N/A')
        ])
    
    table = create_table(f"Found {len(algorithms)} algorithm(s)", headers, rows)
    console.print(table)
    
    console.print("\n[dim]Use 'ga-red algorithms show <name>' for detailed information[/dim]")

def show_algorithm(client: APIClient, args):
    """Show algorithm details"""
    algorithm_name = select_algorithm(client, getattr(args, 'algorithm_name', None))
    if not algorithm_name:
        return
    
    # New API exposes only a list; fetch all and filter client-side
    with console.status(f"[red]Fetching algorithm '{algorithm_name}'...[/red]"):
        algos = client.get("/algorithms")
    if not algos:
        return
    response = None
    for a in (algos if isinstance(algos, list) else algos.get('algorithms', [])):
        if (a.get('name') or '').lower() == algorithm_name.lower():
            response = a
            break
    if not response:
        print_error(f"Algorithm '{algorithm_name}' not found")
        return
    
    if hasattr(args, 'json') and args.json:
        print_json(response, title=f"Algorithm: {algorithm_name}")
        return
    
    # Display algorithm details
    print_panel(f"Algorithm: {algorithm_name}", style="red")
    
    # Basic info
    console.print(f"\n[bold]Name:[/bold] {response.get('name', 'N/A')}")
    console.print(f"[bold]Type:[/bold] {response.get('type', 'N/A')}")
    console.print(f"[bold]Description:[/bold] {response.get('description', 'N/A')}")
    
    # Display config schema if available
    config_schema = response.get('config_schema') or {}
    if config_schema:
        console.print("\n[bold red]Config Schema:[/bold red]")
        console.print(JSON(json.dumps(config_schema)))
    
    # Display diagram if available
    chart = response.get('chart')
    if chart:
        console.print("\n[bold red]Flowchart (Mermaid):[/bold red]")
        console.print(Panel(chart, expand=False))