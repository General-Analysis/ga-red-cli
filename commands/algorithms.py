"""
Algorithms command - View available attack algorithms with consistent verbs
"""

import sys
import argparse
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from utils import (
    APIClient, create_table, console, print_success, print_error,
    print_warning, print_info, print_panel, print_json, select_algorithm
)

def print_algorithms_help():
    """Print algorithms command help using Rich"""
    console.print(Panel.fit(
        "[bold cyan]Algorithms Command[/bold cyan] - View available attack algorithms",
        title="Algorithm Management",
        border_style="cyan"
    ))
    
    console.print("\n[bold]Usage:[/bold]")
    console.print("  ga-red algorithms [cyan]<action>[/cyan] [dim][options][/dim]\n")
    
    # Create actions table
    table = Table(title="Available Actions", show_header=True, header_style="bold cyan")
    table.add_column("Action", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    
    table.add_row("list", "List available algorithms")
    table.add_row("show [name]", "Show algorithm details with params (interactive if no name)")
    
    console.print(table)
    
    console.print("\n[dim]For help on a specific action:[/dim]")
    console.print("  ga-red algorithms [cyan]<action>[/cyan] --help")
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
    with console.status("[cyan]Fetching algorithms...[/cyan]"):
        response = client.get("/attack_algorithms")
    
    if not response:
        return
    
    algorithms = response.get('algorithms', [])
    
    if not algorithms:
        print_warning("No algorithms found")
        return
    
    if hasattr(args, 'json') and args.json:
        print_json(algorithms, title="Algorithms")
        return
    
    # Create table
    headers = ["Name", "Description", "Category"]
    rows = []
    
    for algo in algorithms:
        desc = algo.get('description', 'N/A')
        desc_display = desc[:60] + "..." if len(desc) > 60 else desc
        
        rows.append([
            algo.get('name', 'N/A'),
            desc_display,
            algo.get('category', 'N/A')
        ])
    
    table = create_table(f"Found {len(algorithms)} algorithm(s)", headers, rows)
    console.print(table)
    
    console.print("\n[dim]Use 'ga-red algorithms show <name>' for detailed information[/dim]")

def show_algorithm(client: APIClient, args):
    """Show algorithm details"""
    algorithm_name = select_algorithm(client, getattr(args, 'algorithm_name', None))
    if not algorithm_name:
        return
    
    with console.status(f"[cyan]Fetching algorithm '{algorithm_name}'...[/cyan]"):
        response = client.get(f"/attack_algorithms/{algorithm_name}")
    
    if not response:
        return
    
    if hasattr(args, 'json') and args.json:
        print_json(response, title=f"Algorithm: {algorithm_name}")
        return
    
    # Display algorithm details
    print_panel(f"Algorithm: {algorithm_name}", style="cyan")
    
    # Basic info
    console.print(f"\n[bold]Name:[/bold] {response.get('name', 'N/A')}")
    console.print(f"[bold]Category:[/bold] {response.get('category', 'N/A')}")
    console.print(f"[bold]Description:[/bold] {response.get('description', 'N/A')}")
    
    # Display parameters if available
    params = response.get('parameters', {})
    if params:
        console.print("\n[bold cyan]Parameters:[/bold cyan]")
        
        # Create parameters table
        param_table = Table(show_header=True, header_style="bold")
        param_table.add_column("Parameter", style="cyan")
        param_table.add_column("Type", style="yellow")
        param_table.add_column("Default", style="green")
        param_table.add_column("Description")
        
        for param_name, param_info in params.items():
            param_table.add_row(
                param_name,
                str(param_info.get('type', 'any')),
                str(param_info.get('default', 'N/A')),
                param_info.get('description', '')
            )
        
        console.print(param_table)
    
    # Display example configuration if available
    example = response.get('example_config')
    if example:
        console.print("\n[bold cyan]Example Configuration:[/bold cyan]")
        console.print(Panel(
            Syntax(str(example), "yaml", theme="monokai"),
            expand=False
        ))
    
    # Display additional notes if available
    notes = response.get('notes')
    if notes:
        console.print("\n[bold cyan]Notes:[/bold cyan]")
        console.print(notes)