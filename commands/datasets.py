"""
Datasets command - Manage datasets with consistent verbs
"""

import sys
import argparse
import json
import csv
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
        "[bold red]Datasets Command[/bold red] - Manage datasets and their entries",
        title="Dataset Management",
        border_style="red"
    ))
    
    console.print("\n[bold]Usage:[/bold]")
    console.print("  ga-red datasets [red]<action>[/red] [dim][options][/dim]\n")
    
    # Create actions table
    table = Table(title="Available Actions", show_header=True, header_style="bold red")
    table.add_column("Action", style="red", no_wrap=True)
    table.add_column("Description", style="white")
    
    table.add_row("list", "List all datasets")
    table.add_row("show [name]", "Show dataset details (interactive if no name)")
    table.add_row("entries [name]", "View/paginate entries (interactive if no name)")
    table.add_row("export [name]", "Export dataset to JSON/CSV (interactive if no name)")
    table.add_row("create [name] [csv_file]", "Create dataset from CSV (goal column required)")
    table.add_row("delete [name]", "Delete dataset (interactive if no name)")
    
    console.print(table)
    
    console.print("\n[dim]For help on a specific action:[/dim]")
    console.print("  ga-red datasets [red]<action>[/red] --help")
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
    create_parser = subparsers.add_parser('create', help='Create dataset from CSV file')
    create_parser.add_argument('name', help='Dataset name')
    create_parser.add_argument('csv_file', help='Path to CSV file with goal column (prompt column optional)')
    create_parser.add_argument('--description', '-d', help='Dataset description')
    
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
    with console.status("[red]Fetching datasets...[/red]"):
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
    headers = ["ID", "Name", "Entries", "Description", "Created"]
    rows = []
    
    for dataset in datasets:
        desc = dataset.get('description', 'N/A')
        if desc is None:
            desc = 'N/A'
        desc_display = desc[:40] + "..." if len(desc) > 40 else desc
        
        rows.append([
            str(dataset.get('id', '')),
            dataset.get('name', 'N/A'),
            str(dataset.get('size', dataset.get('entries_count', 0))),
            desc_display,
            format_datetime(dataset.get('created_at', ''))
        ])
    
    table = create_table(f"Found {len(datasets)} dataset(s)", headers, rows)
    console.print(table)

def show_dataset(client: APIClient, args):
    """Show dataset details"""
    dataset_id = select_dataset(client, getattr(args, 'dataset_name', None))
    if not dataset_id:
        return
    
    with console.status(f"[red]Fetching dataset {dataset_id}...[/red]"):
        data = client.get(f"/datasets/{dataset_id}")
    
    if not data:
        return
    
    if hasattr(args, 'json') and args.json:
        print_json(data, title=f"Dataset: {data.get('name', 'N/A')}")
        return
    
    # Display dataset details
    print_panel(f"Dataset: {data.get('name', 'N/A')} (id={data.get('id', dataset_id)})", style="red")
    
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
    dataset_id = select_dataset(client, getattr(args, 'dataset_name', None))
    if not dataset_id:
        return
    
    limit = getattr(args, 'limit', 10)
    offset = getattr(args, 'offset', 0)
    
    # Build endpoint with parameters
    endpoint = f"/datasets/{dataset_id}/entries"
    params = []
    if limit:
        params.append(f"limit={limit}")
    if offset:
        params.append(f"offset={offset}")
    if params:
        endpoint += "?" + "&".join(params)
    
    with console.status(f"[red]Fetching entries for dataset {dataset_id}...[/red]"):
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
        print_json({'dataset_id': dataset_id, 'entries': entries, 'total': total})
        return
    
    if not entries:
        print_warning("No entries found")
        return
    
    # Display entries
    print_panel(
        f"Dataset ID: {dataset_id} - Showing {len(entries)} entries (offset={offset})",
        style="red"
    )
    
    for idx, entry in enumerate(entries, 1 + offset):
        console.print(f"\n[bold]Entry {idx}:[/bold]")
        console.print(f"  Prompt: {entry.get('prompt', '')}")
        console.print(f"  Goal: {entry.get('goal', '')}")
    
    if limit and len(entries) == limit:
        console.print(f"\n[dim]Use --offset {offset + limit} to see more entries[/dim]")

def export_dataset(client: APIClient, args):
    """Export dataset to file"""
    dataset_id = select_dataset(client, getattr(args, 'dataset_name', None))
    if not dataset_id:
        return
    
    with console.status(f"[red]Fetching dataset {dataset_id}...[/red]"):
        data = client.get(f"/datasets/{dataset_id}")
    
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
    """Create a new dataset from CSV file"""
    csv_file = Path(args.csv_file)
    
    # Check if file exists
    if not csv_file.exists():
        print_error(f"CSV file not found: {csv_file}")
        return
    
    # Check file extension
    if csv_file.suffix.lower() != '.csv':
        print_warning(f"File '{csv_file}' does not have .csv extension. Proceeding anyway...")
    
    entries = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check if required columns exist
            if reader.fieldnames is None:
                print_error("CSV file appears to be empty")
                return
            
            # Convert fieldnames to lowercase for case-insensitive comparison
            fieldnames_lower = [field.lower() for field in reader.fieldnames]
            
            # Only goal column is required now
            if 'goal' not in fieldnames_lower:
                print_error("CSV file must have a 'goal' column")
                print_info(f"Found columns: {', '.join(reader.fieldnames)}")
                return
            
            # Find the actual column names (preserve original case)
            prompt_col = None
            goal_col = None
            for field in reader.fieldnames:
                if field.lower() == 'prompt':
                    prompt_col = field
                elif field.lower() == 'goal':
                    goal_col = field
            
            # Check if prompt column exists (no warning needed, this is expected behavior)
            has_prompt_column = prompt_col is not None
            
            # Read entries
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                # Get prompt from column if it exists, otherwise use empty string
                prompt = row.get(prompt_col, '').strip() if prompt_col else ''
                goal = row.get(goal_col, '').strip()
                
                # Skip rows without goals
                if not goal:
                    print_warning(f"Row {row_num}: Missing goal, skipping...")
                    continue
                
                entries.append({
                    'prompt': prompt,  # Will be empty if no prompt column
                    'goal': goal
                })
        
        if not entries:
            print_error("No valid entries found in CSV file")
            return
        
        console.print(f"[green]Loaded {len(entries)} valid entries from {csv_file}[/green]")
        
    except Exception as e:
        print_error(f"Failed to read CSV file: {e}")
        return
    
    # Prepare dataset data
    dataset_data = {
        'name': args.name,
        'description': getattr(args, 'description', f'Dataset created from {csv_file.name}'),
        'entries': entries
    }
    
    # Create dataset
    with console.status(f"[red]Creating dataset '{args.name}' with {len(entries)} entries...[/red]"):
        response = client.post("/datasets", dataset_data)
    
    if response:
        print_success(f"Dataset '{args.name}' created successfully")
        
        # Show brief info
        info_lines = []
        info_lines.append(f"[bold]Name:[/bold] {response.get('name', args.name)}")
        info_lines.append(f"[bold]Description:[/bold] {response.get('description', 'N/A')}")
        info_lines.append(f"[bold]Entries:[/bold] {response.get('size', len(entries))}")
        info_lines.append(f"[bold]Source:[/bold] {csv_file.name}")
        
        print_panel("\n".join(info_lines), title="Created Dataset", style="green")

def delete_dataset(client: APIClient, args):
    """Delete a dataset"""
    dataset_id = select_dataset(client, getattr(args, 'dataset_name', None))
    if not dataset_id:
        return
    
    if not getattr(args, 'force', False):
        if not confirm_action(f"Delete dataset id '{dataset_id}'?"):
            print_info("Deletion cancelled")
            return
    
    if client.delete(f"/datasets/{dataset_id}"):
        print_success(f"Dataset {dataset_id} deleted")
    else:
        print_error(f"Failed to delete dataset {dataset_id}")