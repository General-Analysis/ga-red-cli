"""
Algorithms command - List and view available attack algorithms
"""

import sys
import argparse
from rich.panel import Panel
from rich.table import Table
from utils import (
    APIClient, create_table, console, print_success, print_error,
    print_warning, print_info, print_panel, print_json
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
    
    table.add_row("list", "List all available algorithms")
    table.add_row("get", "Get algorithm details")
    
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
        add_help=False  # We'll handle help ourselves
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
    list_parser = subparsers.add_parser('list', help='List all available algorithms')
    list_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get algorithm details')
    get_parser.add_argument('algorithm_name', help='Algorithm name')
    get_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

def execute(args):
    """Execute algorithms command"""
    # Check if help was requested
    if hasattr(args, 'help') and args.help:
        print_algorithms_help()
        return
        
    client = APIClient()
    
    if not args.action:
        print_algorithms_help()
        return
    
    if args.action == 'list':
        list_algorithms(client, args)
    elif args.action == 'get':
        get_algorithm(client, args)

def list_algorithms(client: APIClient, args):
    """List all available algorithms"""
    with console.status("[cyan]Fetching algorithms...[/cyan]"):
        response = client.get("/attack_algorithms")
    
    if not response:
        return
    
    # Extract algorithms list from response
    algorithms = response if isinstance(response, list) else response.get('algorithms', [])
    
    if not algorithms:
        print_warning("No algorithms found")
        return
    
    # Output as JSON if requested
    if hasattr(args, 'json') and args.json:
        print_json(algorithms, title="Algorithms")
        return
    
    # Create table
    headers = ["Name", "Description"]
    rows = []
    
    for algo in algorithms:
        name = algo.get('name', 'N/A')
        description = algo.get('description', 'N/A')
        # Truncate description if too long
        desc_display = description[:80] + "..." if len(description) > 80 else description
        
        rows.append([
            name,
            desc_display
        ])
    
    table = create_table(f"Found {len(algorithms)} algorithm(s)", headers, rows)
    console.print(table)
    
    # Print usage tip
    console.print(f"\n[dim]Use 'ga-red algorithms get <name>' for detailed information[/dim]")

def get_algorithm(client: APIClient, args):
    """Get algorithm details"""
    algorithm_name = args.algorithm_name
    
    with console.status(f"[cyan]Fetching algorithm '{algorithm_name}'...[/cyan]"):
        data = client.get(f"/attack_algorithms/{algorithm_name}")
    
    if not data:
        return
    
    # Output as JSON if requested
    if hasattr(args, 'json') and args.json:
        print_json(data, title=f"Algorithm: {algorithm_name}")
        return
    
    # Pretty print algorithm details
    algorithm = data
    
    # Create algorithm info panel
    info_lines = []
    info_lines.append(f"[bold]Name:[/bold] {algorithm.get('name', 'N/A')}")
    info_lines.append(f"[bold]Description:[/bold] {algorithm.get('description', 'N/A')}")
    
    # Show config schema if available
    config_schema = algorithm.get('config_schema')
    if config_schema:
        info_lines.append(f"[bold]Configurable:[/bold] Yes")
        info_lines.append(f"[bold]Parameters:[/bold] {len(config_schema.get('properties', {}))} available")
    else:
        info_lines.append(f"[bold]Configurable:[/bold] No")
    
    print_panel("\n".join(info_lines), title=f"Algorithm: {algorithm.get('name', 'Unknown')}", style="cyan")
    
    # Show configuration schema details if available
    if config_schema and config_schema.get('properties'):
        console.print(f"\n[bold cyan]Configuration Parameters:[/bold cyan]")
        
        properties = config_schema.get('properties', {})
        for param_name, param_info in properties.items():
            param_type = param_info.get('type', 'unknown')
            param_desc = param_info.get('description', 'No description')
            param_default = param_info.get('default', 'No default')
            
            console.print(f"\n  [bold]{param_name}[/bold] ([cyan]{param_type}[/cyan])")
            console.print(f"    {param_desc}")
            if param_default != 'No default':
                console.print(f"    [dim]Default: {param_default}[/dim]")
