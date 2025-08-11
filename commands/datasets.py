"""
Datasets command - Manage datasets with consistent verbs
"""

import sys
import argparse
import json
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from utils import (
    APIClient, create_table, console, print_success, print_error,
    print_warning, print_info, print_panel, print_json, confirm_action,
    select_dataset, format_datetime, save_to_csv
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
    table.add_row("show [name]", "Show dataset details (interactive if no name)")
    table.add_row("entries [name]", "View/paginate entries (interactive if no name)")
    table.add_row("export [name]", "Export dataset to JSON/CSV (interactive if no name)")
    table.add_row("create", "Create new dataset")
    table.add_row("delete [name]", "Delete dataset (interactive if no name)")
    
    console.print(table)
    
    console.print("\n[dim]For help on a specific action:[/dim]")
    console.print("  ga-red datasets [cyan]<action>[/cyan] --help")
    console.print()

def add_parser(subparsers):
    """Add datasets command parser"""
    parser = subparsers.add_parser(
        'datasets',
        help='Manage datasets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Manage datasets and their entries',
        add_help=False
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
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show dataset details')
    show_parser.add_argument('dataset_name', nargs='?', help='Dataset name (interactive if not provided)')
    show_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Entries command
    entries_parser = subparsers.add_parser('entries', help='View dataset entries')
    entries_parser.add_argument('dataset_name', nargs='?', help='Dataset name (interactive if not provided)')
    entries_parser.add_argument('--limit', type=int, default=10, help='Number of entries to show')
    entries_parser.add_argument('--offset', type=int, default=0, help='Number of entries to skip')
    entries_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export dataset')
    export_parser.add_argument('dataset_name', nargs='?', help='Dataset name (interactive if not provided)')
    export_parser.add_argument('--output', '-o', required=True, help='Output file path')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new dataset')
    create_parser.add_argument('name', help='Dataset name')
    create_parser.add_argument('--description', '-d', help='Dataset description')
    create_parser.add_argument('--entries-file', help='JSON file with initial entries')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete dataset')
    delete_parser.add_argument('dataset_name', nargs='?', help='Dataset name (interactive if not provided)')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')

def execute(args):
    """Execute datasets command"""
    if hasattr(args, 'help') and args.help:
        print_datasets_help()
        return
        
    client = APIClient()
    
    if not args.action:
        print_datasets_help()
        return
    
    if args.action == 'list':
        list_datasets(client, args)
    elif args.action == 'show':
        show_dataset(client, args)
    elif args.action == 'entries':
        show_entries(client, args)
    elif args.action == 'export':
        export_dataset(client, args)
    elif args.action == 'create':
        create_dataset(client, args)
    elif args.action == 'delete':
        delete_dataset(client, args)

def list_datasets(client: APIClient, args):
    """List all datasets"""
    with console.status("[cyan]Fetching datasets...[/cyan]"):
        response = client.get("/datasets")
    
    if not response:
        return
    
    datasets = response.get('datasets', response) if isinstance(response, dict) else response
    
    if not datasets:
        print_warning("No datasets found")
        return
    
    if hasattr(args, 'json') and args.json:
        print_json(datasets, title="Datasets")
        return
    
    # Create table
    headers = ["Name", "Entries", "Description", "Created"]
    rows = []
    
    for dataset in datasets:
        desc = dataset.get('description', 'N/A')
        desc_display = desc[:40] + "..." if len(desc) > 40 else desc
        
        rows.append([
            dataset.get('name', 'N/A'),
            str(dataset.get('size', dataset.get('entries_count', 0))),
            desc_display,
            format_datetime(dataset.get('created_at', ''))
        ])
    
    table = create_table(f"Found {len(datasets)} dataset(s)", headers, rows)
    console.print(table)

def show_dataset(client: APIClient, args):
    """Show dataset details"""
    dataset_name = select_dataset(client, getattr(args, 'dataset_name', None))
    if not dataset_name:
        return
    
    with console.status(f"[cyan]Fetching dataset '{dataset_name}'...[/cyan]"):
        data = client.get(f"/datasets/{dataset_name}")
    
    if not data:
        return
    
    if hasattr(args, 'json') and args.json:
        print_json(data, title=f"Dataset: {dataset_name}")
        return
    
    # Display dataset details
    print_panel(f"Dataset: {dataset_name}", style="cyan")
    
    details = []
    details.append(f"Name: {data.get('name', 'N/A')}")
    details.append(f"Description: {data.get('description', 'N/A')}")
    details.append(f"Entries: {data.get('size', data.get('entries_count', 0))}")
    details.append(f"Created: {format_datetime(data.get('created_at', ''))}")
    
    console.print("\n".join(details))
    
    # Show sample entries if available
    entries = data.get('entries', [])
    if entries:
        console.print("\n[bold]Sample Entries:[/bold]")
        for idx, entry in enumerate(entries[:3], 1):
            console.print(f"\n  Entry {idx}:")
            console.print(f"    Prompt: {entry.get('prompt', '')[:100]}...")
            console.print(f"    Goal: {entry.get('goal', '')[:100]}...")

def show_entries(client: APIClient, args):
    """Show dataset entries with pagination"""
    dataset_name = select_dataset(client, getattr(args, 'dataset_name', None))
    if not dataset_name:
        return
    
    limit = getattr(args, 'limit', 10)
    offset = getattr(args, 'offset', 0)
    
    # Build endpoint with parameters
    endpoint = f"/datasets/{dataset_name}/entries"
    params = []
    if limit:
        params.append(f"limit={limit}")
    if offset:
        params.append(f"offset={offset}")
    if params:
        endpoint += "?" + "&".join(params)
    
    with console.status(f"[cyan]Fetching entries for '{dataset_name}'...[/cyan]"):
        data = client.get(endpoint)
    
    if not data:
        return
    
    # Handle different response formats
    if isinstance(data, list):
        entries = data
        total = len(entries)
    else:
        entries = data.get('entries', [])
        total = data.get('total', len(entries))
    
    if hasattr(args, 'json') and args.json:
        print_json({'dataset': dataset_name, 'entries': entries, 'total': total})
        return
    
    if not entries:
        print_warning("No entries found")
        return
    
    # Display entries
    print_panel(
        f"Dataset: {dataset_name} - Showing {len(entries)} entries (offset={offset})",
        style="cyan"
    )
    
    for idx, entry in enumerate(entries, 1 + offset):
        console.print(f"\n[bold]Entry {idx}:[/bold]")
        console.print(f"  Prompt: {entry.get('prompt', '')}")
        console.print(f"  Goal: {entry.get('goal', '')}")
    
    if limit and len(entries) == limit:
        console.print(f"\n[dim]Use --offset {offset + limit} to see more entries[/dim]")

def export_dataset(client: APIClient, args):
    """Export dataset to file"""
    dataset_name = select_dataset(client, getattr(args, 'dataset_name', None))
    if not dataset_name:
        return
    
    with console.status(f"[cyan]Fetching dataset '{dataset_name}'...[/cyan]"):
        data = client.get(f"/datasets/{dataset_name}")
    
    if not data:
        return
    
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if args.format == 'csv':
        entries = data.get('entries', [])
        
        if not entries:
            print_warning("No entries to export")
            return
        
        fieldnames = ['index', 'prompt', 'goal']
        csv_data = []
        
        for idx, entry in enumerate(entries, 1):
            csv_data.append({
                'index': idx,
                'prompt': entry.get('prompt', ''),
                'goal': entry.get('goal', '')
            })
        
        save_to_csv(csv_data, str(output_file), fieldnames)
    else:
        # Export as JSON
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print_success(f"Dataset exported to: {output_file.absolute()}")

def create_dataset(client: APIClient, args):
    """Create a new dataset"""
    dataset_data = {
        'name': args.name,
        'description': getattr(args, 'description', '')
    }
    
    # Load entries from file if provided
    if getattr(args, 'entries_file', None):
        entries_file = Path(args.entries_file)
        if not entries_file.exists():
            print_error(f"Entries file not found: {entries_file}")
            return
        
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
            
            dataset_data['entries'] = entries
            console.print(f"[green]Loaded {len(entries)} entries from {args.entries_file}[/green]")
            
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON in entries file: {e}")
            return
        except Exception as e:
            print_error(f"Failed to load entries file: {e}")
            return
    
    with console.status(f"[cyan]Creating dataset '{args.name}'...[/cyan]"):
        response = client.post("/datasets", dataset_data)
    
    if response:
        print_success(f"Dataset '{args.name}' created successfully")
        
        # Show brief info
        info_lines = []
        info_lines.append(f"[bold]Name:[/bold] {response.get('name', args.name)}")
        info_lines.append(f"[bold]Description:[/bold] {response.get('description', 'N/A')}")
        info_lines.append(f"[bold]Entries:[/bold] {len(response.get('entries', []))}")
        
        print_panel("\n".join(info_lines), title="Created Dataset", style="green")

def delete_dataset(client: APIClient, args):
    """Delete a dataset"""
    dataset_name = select_dataset(client, getattr(args, 'dataset_name', None))
    if not dataset_name:
        return
    
    if not getattr(args, 'force', False):
        if not confirm_action(f"Delete dataset '{dataset_name}'?"):
            print_info("Deletion cancelled")
            return
    
    if client.delete(f"/datasets/{dataset_name}"):
        print_success(f"Dataset '{dataset_name}' deleted")
    else:
        print_error(f"Failed to delete dataset '{dataset_name}'")