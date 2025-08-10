"""
Datasets command - Manage datasets and their entries
"""

import sys
import argparse
import json
from rich.panel import Panel
from rich.table import Table
from utils import (
    APIClient, create_table, console, print_success, print_error,
    print_warning, print_info, print_panel, print_json, confirm_action
)

def print_datasets_help():
    """Print datasets command help using Rich"""
    console.print(Panel.fit(
        "[bold cyan]Datasets Command[/bold cyan] - Manage datasets and their entries",
        title="Dataset Management",
        border_style="cyan"
    ))
    
    console.print("\n[bold]Usage:[/bold]")
    console.print("  ga-red datasets [cyan]<action>[/cyan] [dim][options][/dim]\n")
    
    # Create actions table
    table = Table(title="Available Actions", show_header=True, header_style="bold cyan")
    table.add_column("Action", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    
    table.add_row("list", "List all datasets")
    table.add_row("get", "Get dataset details and entries")
    table.add_row("create", "Create a new dataset")
    table.add_row("delete", "Delete a dataset")
    table.add_row("entries", "View dataset entries with pagination")
    table.add_row("add-entries", "Add entries to an existing dataset")
    
    console.print(table)
    
    console.print("\n[dim]For help on a specific action:[/dim]")
    console.print("  ga-red datasets [cyan]<action>[/cyan] --help")
    console.print()

def add_parser(subparsers):
    """Add datasets command parser"""
    parser = subparsers.add_parser(
        'datasets',
        help='Manage datasets and their entries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Manage datasets and their entries',
        add_help=False  # We'll handle help ourselves
    )
    
    # Check if user is asking for help at datasets level
    if len(sys.argv) >= 3 and sys.argv[1] == 'datasets' and sys.argv[2] in ['--help', '-h']:
        print_datasets_help()
        sys.exit(0)
    
    # Add help argument
    parser.add_argument('--help', '-h', action='store_true', help='Show help message')
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all datasets')
    list_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get dataset details and entries')
    get_parser.add_argument('dataset_name', help='Dataset name')
    get_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    get_parser.add_argument(
        '--entries-only',
        action='store_true',
        help='Show only entries, not dataset metadata'
    )
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new dataset')
    create_parser.add_argument('name', help='Dataset name')
    create_parser.add_argument(
        '--description', '-d',
        help='Dataset description'
    )
    create_parser.add_argument(
        '--entries-file',
        help='JSON file containing initial entries (array of {prompt, goal} objects)'
    )
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a dataset')
    delete_parser.add_argument('dataset_name', help='Dataset name to delete')
    delete_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Skip confirmation'
    )
    
    # Entries command
    entries_parser = subparsers.add_parser('entries', help='View dataset entries with pagination')
    entries_parser.add_argument('dataset_name', help='Dataset name')
    entries_parser.add_argument(
        '--limit', '-l',
        type=int,
        help='Number of entries to display'
    )
    entries_parser.add_argument(
        '--offset', '-o',
        type=int,
        default=0,
        help='Number of entries to skip (default: 0)'
    )
    entries_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    # Add entries command
    add_entries_parser = subparsers.add_parser('add-entries', help='Add entries to an existing dataset')
    add_entries_parser.add_argument('dataset_name', help='Dataset name')
    add_entries_parser.add_argument('entries_file', help='JSON file containing entries to add')

def execute(args):
    """Execute datasets command"""
    # Check if help was requested
    if hasattr(args, 'help') and args.help:
        print_datasets_help()
        return
        
    client = APIClient()
    
    if not args.action:
        print_datasets_help()
        return
    
    if args.action == 'list':
        list_datasets(client, args)
    elif args.action == 'get':
        get_dataset(client, args)
    elif args.action == 'create':
        create_dataset(client, args)
    elif args.action == 'delete':
        delete_dataset(client, args)
    elif args.action == 'entries':
        get_dataset_entries(client, args)
    elif args.action == 'add-entries':
        add_dataset_entries(client, args)

def list_datasets(client: APIClient, args):
    """List all datasets"""
    with console.status("[cyan]Fetching datasets...[/cyan]"):
        response = client.get("/datasets")
    
    if not response:
        return
    
    datasets = response if isinstance(response, list) else response.get('datasets', [])
    
    if not datasets:
        print_warning("No datasets found")
        return
    
    # Output as JSON if requested
    if hasattr(args, 'json') and args.json:
        print_json(datasets, title="Datasets")
        return
    
    # Create table
    headers = ["Name", "Description", "Size", "Created", "Updated"]
    rows = []
    
    for dataset in datasets:
        name = dataset.get('name', 'N/A')
        description = dataset.get('description', '')
        desc_display = description[:40] + "..." if description and len(description) > 40 else description or 'N/A'
        size = dataset.get('size', 0)
        created = dataset.get('created_at', '')[:16] if dataset.get('created_at') else 'N/A'
        updated = dataset.get('updated_at', '')[:16] if dataset.get('updated_at') else 'N/A'
        
        rows.append([
            name,
            desc_display,
            str(size),
            created,
            updated
        ])
    
    table = create_table(f"Found {len(datasets)} dataset(s)", headers, rows)
    console.print(table)
    
    # Print usage tip
    console.print(f"\n[dim]Use 'ga-red datasets get <name>' for detailed information[/dim]")

def get_dataset(client: APIClient, args):
    """Get dataset details"""
    dataset_name = args.dataset_name
    
    with console.status(f"[cyan]Fetching dataset '{dataset_name}'...[/cyan]"):
        data = client.get(f"/datasets/{dataset_name}")
    
    if not data:
        return
    
    # Output as JSON if requested
    if hasattr(args, 'json') and args.json:
        print_json(data, title=f"Dataset: {dataset_name}")
        return
    
    dataset = data
    entries = dataset.get('entries', [])
    
    if args.entries_only:
        # Show only entries
        if entries:
            console.print(f"\n[bold cyan]Entries for '{dataset_name}' ({len(entries)} total):[/bold cyan]")
            for i, entry in enumerate(entries[:10], 1):  # Show first 10
                console.print(f"\n  [bold]Entry {i}:[/bold]")
                console.print(f"    [dim]Goal:[/dim] {entry.get('goal', 'N/A')}")
                console.print(f"    [dim]Prompt:[/dim] {entry.get('prompt', 'N/A')[:100]}...")
            if len(entries) > 10:
                console.print(f"\n  [dim]... and {len(entries) - 10} more entries[/dim]")
        else:
            print_warning("No entries found")
        return
    
    # Create dataset info panel
    info_lines = []
    info_lines.append(f"[bold]Name:[/bold] {dataset.get('name', 'N/A')}")
    info_lines.append(f"[bold]Description:[/bold] {dataset.get('description', 'N/A')}")
    info_lines.append(f"[bold]Size:[/bold] {dataset.get('size', 0)} entries")
    info_lines.append(f"[bold]Created:[/bold] {dataset.get('created_at', 'N/A')}")
    info_lines.append(f"[bold]Updated:[/bold] {dataset.get('updated_at', 'N/A')}")
    
    print_panel("\n".join(info_lines), title=f"Dataset: {dataset_name}", style="cyan")
    
    # Show sample entries
    if entries:
        console.print(f"\n[bold cyan]Sample entries ({len(entries)} total):[/bold cyan]")
        for i, entry in enumerate(entries[:3], 1):
            console.print(f"\n  [bold]Entry {i}:[/bold]")
            console.print(f"    [dim]Goal:[/dim] {entry.get('goal', 'N/A')}")
            console.print(f"    [dim]Prompt:[/dim] {entry.get('prompt', 'N/A')[:100]}...")
        
        if len(entries) > 3:
            console.print(f"\n  [dim]... and {len(entries) - 3} more entries[/dim]")
            console.print(f"  [dim]Use 'ga-red datasets entries {dataset_name}' to see all entries[/dim]")

def create_dataset(client: APIClient, args):
    """Create a new dataset"""
    dataset_data = {
        "name": args.name,
        "description": args.description or "",
        "entries": []
    }
    
    # Load entries from file if provided
    if args.entries_file:
        try:
            with open(args.entries_file, 'r') as f:
                entries = json.load(f)
            
            # Validate entries format
            if not isinstance(entries, list):
                print_error("Entries file must contain a JSON array")
                return
            
            for i, entry in enumerate(entries):
                if not isinstance(entry, dict) or 'prompt' not in entry or 'goal' not in entry:
                    print_error(f"Entry {i+1} must have 'prompt' and 'goal' fields")
                    return
            
            dataset_data["entries"] = entries
            console.print(f"[green]Loaded {len(entries)} entries from {args.entries_file}[/green]")
            
        except FileNotFoundError:
            print_error(f"Entries file not found: {args.entries_file}")
            return
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON in entries file: {e}")
            return
    
    with console.status(f"[cyan]Creating dataset '{args.name}'...[/cyan]"):
        response = client.post("/datasets", json=dataset_data)
    
    if response:
        entries_count = len(response.get('entries', []))
        print_success(f"Dataset '{args.name}' created successfully with {entries_count} entries")
        
        # Show brief info
        info_lines = []
        info_lines.append(f"[bold]Name:[/bold] {response.get('name')}")
        info_lines.append(f"[bold]Description:[/bold] {response.get('description', 'N/A')}")
        info_lines.append(f"[bold]Entries:[/bold] {entries_count}")
        
        print_panel("\n".join(info_lines), title="Created Dataset", style="green")

def delete_dataset(client: APIClient, args):
    """Delete a dataset"""
    dataset_name = args.dataset_name
    
    if not args.force:
        if not confirm_action(f"[red]Are you sure you want to delete dataset '{dataset_name}' and all its entries?[/red]"):
            print_warning("Cancelled")
            return
    
    with console.status(f"[red]Deleting dataset '{dataset_name}'...[/red]"):
        response = client.delete(f"/datasets/{dataset_name}")
    
    if response:
        print_success(f"Dataset '{dataset_name}' deleted successfully")

def get_dataset_entries(client: APIClient, args):
    """Get dataset entries with pagination"""
    dataset_name = args.dataset_name
    endpoint = f"/datasets/{dataset_name}/entries"
    
    # Build query parameters manually
    query_params = []
    if args.limit:
        query_params.append(f"limit={args.limit}")
    if args.offset:
        query_params.append(f"offset={args.offset}")
    
    if query_params:
        endpoint += "?" + "&".join(query_params)
    
    with console.status(f"[cyan]Fetching entries for '{dataset_name}'...[/cyan]"):
        entries = client.get(endpoint)
    
    if not entries:
        return
    
    if not isinstance(entries, list):
        entries = entries.get('entries', [])
    
    if not entries:
        print_warning("No entries found")
        return
    
    # Output as JSON if requested
    if hasattr(args, 'json') and args.json:
        print_json(entries, title=f"Entries for {dataset_name}")
        return
    
    # Create table
    headers = ["ID", "Goal", "Prompt", "Created"]
    rows = []
    
    for entry in entries:
        entry_id = entry.get('id', 'N/A')
        goal = entry.get('goal', 'N/A')
        goal_display = goal[:40] + "..." if len(goal) > 40 else goal
        prompt = entry.get('prompt', 'N/A')
        prompt_display = prompt[:50] + "..." if len(prompt) > 50 else prompt
        created = entry.get('created_at', '')[:16] if entry.get('created_at') else 'N/A'
        
        rows.append([
            str(entry_id),
            goal_display,
            prompt_display,
            created
        ])
    
    title = f"Entries for '{dataset_name}'"
    if args.limit or args.offset:
        title += f" (limit={args.limit or 'all'}, offset={args.offset})"
    
    table = create_table(title, headers, rows)
    console.print(table)
    
    if args.limit and len(entries) == args.limit:
        console.print(f"\n[dim]Use --offset {args.offset + args.limit} to see more entries[/dim]")

def add_dataset_entries(client: APIClient, args):
    """Add entries to an existing dataset"""
    dataset_name = args.dataset_name
    entries_file = args.entries_file
    
    # Load entries from file
    try:
        with open(entries_file, 'r') as f:
            entries = json.load(f)
        
        # Validate entries format
        if not isinstance(entries, list):
            print_error("Entries file must contain a JSON array")
            return
        
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict) or 'prompt' not in entry or 'goal' not in entry:
                print_error(f"Entry {i+1} must have 'prompt' and 'goal' fields")
                return
        
        console.print(f"[green]Loaded {len(entries)} entries from {entries_file}[/green]")
        
    except FileNotFoundError:
        print_error(f"Entries file not found: {entries_file}")
        return
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in entries file: {e}")
        return
    
    with console.status(f"[cyan]Adding {len(entries)} entries to '{dataset_name}'...[/cyan]"):
        response = client.post(f"/datasets/{dataset_name}/entries", json=entries)
    
    if response:
        added_count = len(response) if isinstance(response, list) else len(response.get('entries', []))
        print_success(f"Added {added_count} entries to dataset '{dataset_name}'")
