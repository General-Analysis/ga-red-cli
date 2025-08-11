"""
Jobs command - Manage jobs with consistent verbs
"""

import sys
import argparse
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from utils import (
    APIClient, format_datetime, format_status_plain, print_json, 
    confirm_action, create_table, console, print_success, print_error,
    print_warning, print_info, print_panel, select_job, format_status,
    load_yaml_config, save_to_csv
)

def print_jobs_help():
    """Print jobs command help using Rich"""
    console.print(Panel.fit(
        "[bold cyan]Jobs Command[/bold cyan] - Manage REDit jobs",
        title="Jobs Management",
        border_style="cyan"
    ))
    
    console.print("\n[bold]Usage:[/bold]")
    console.print("  ga-red jobs [cyan]<action>[/cyan] [dim][options][/dim]\n")
    
    # Create actions table
    table = Table(title="Available Actions", show_header=True, header_style="bold cyan")
    table.add_column("Action", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    
    table.add_row("list", "List all jobs with filters")
    table.add_row("show [id]", "Show job details (interactive if no id)")
    table.add_row("results [id]", "Get results with trajectories")
    table.add_row("export [id]", "Export results to CSV/JSON")
    table.add_row("attach [id]", "Attach to running job")
    table.add_row("delete [id]", "Delete job(s)")
    table.add_row("run <config>", "Start new job from config")
    
    console.print(table)
    
    console.print("\n[dim]For help on a specific action:[/dim]")
    console.print("  ga-red jobs [cyan]<action>[/cyan] --help")
    console.print()

def add_parser(subparsers):
    """Add jobs command parser"""
    parser = subparsers.add_parser(
        'jobs',
        help='Manage jobs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Manage REDit jobs',
        add_help=False
    )
    
    # Check if user is asking for help at jobs level
    if len(sys.argv) >= 3 and sys.argv[1] == 'jobs' and sys.argv[2] in ['--help', '-h']:
        print_jobs_help()
        sys.exit(0)
    
    # Add help argument
    parser.add_argument('--help', '-h', action='store_true', help='Show help message')
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all jobs with filters')
    list_parser.add_argument('--limit', '-l', type=int, help='Limit number of jobs')
    list_parser.add_argument('--status', '-s', 
        choices=['pending', 'running', 'completed', 'failed', 'error'],
        help='Filter by status')
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show job details')
    show_parser.add_argument('job_id', type=int, nargs='?', help='Job ID (interactive if not provided)')
    show_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Results command
    results_parser = subparsers.add_parser('results', help='Get results with trajectories')
    results_parser.add_argument('job_id', type=int, nargs='?', help='Job ID (interactive if not provided)')
    results_parser.add_argument('--json', action='store_true', help='Output as JSON')
    results_parser.add_argument('--successful', action='store_true', help='Show only successful attacks')
    results_parser.add_argument('--failed', action='store_true', help='Show only failed attacks')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export results to CSV/JSON')
    export_parser.add_argument('job_id', type=int, nargs='?', help='Job ID (interactive if not provided)')
    export_parser.add_argument('--csv', type=str, help='Export to CSV file')
    export_parser.add_argument('--json-file', type=str, help='Export to JSON file')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='json', help='Export format')
    
    # Attach command
    attach_parser = subparsers.add_parser('attach', help='Attach to running job')
    attach_parser.add_argument('job_id', type=int, nargs='?', help='Job ID (interactive if not provided)')
    attach_parser.add_argument('--interval', '-i', type=int, default=5, 
        help='Status check interval in seconds (default: 5)')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete job(s)')
    delete_parser.add_argument('job_id', type=int, nargs='?', help='Job ID (interactive if not provided)')
    delete_parser.add_argument('--all', action='store_true', help='Delete all jobs')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Start new job from config')
    run_parser.add_argument('config_file', help='Configuration file (YAML)')
    run_parser.add_argument('--dry-run', action='store_true', help='Validate config without running')
    run_parser.add_argument('--attach', action='store_true', help='Attach to job after starting')

def execute(args):
    """Execute jobs command"""
    if hasattr(args, 'help') and args.help:
        print_jobs_help()
        return
        
    client = APIClient()
    
    if not args.action:
        print_jobs_help()
        return
    
    if args.action == 'list':
        list_jobs(client, args)
    elif args.action == 'show':
        show_job(client, args)
    elif args.action == 'results':
        show_results(client, args)
    elif args.action == 'export':
        export_results(client, args)
    elif args.action == 'attach':
        attach_to_job(client, args)
    elif args.action == 'delete':
        delete_job(client, args)
    elif args.action == 'run':
        run_job(client, args)

def list_jobs(client: APIClient, args):
    """List all jobs"""
    with console.status("[cyan]Fetching jobs...[/cyan]"):
        response = client.get("/jobs")
    
    if not response:
        return
    
    jobs = response.get('jobs', [])
    
    # Filter by status if specified
    if hasattr(args, 'status') and args.status:
        jobs = [j for j in jobs if j.get('status') == args.status]
    
    # Apply limit if specified
    if hasattr(args, 'limit') and args.limit:
        jobs = jobs[:args.limit]
    
    if not jobs:
        print_warning("No jobs found")
        return
    
    # Output as JSON if requested
    if hasattr(args, 'json') and args.json:
        print_json(jobs, title="Jobs")
        return
    
    # Create table
    headers = ["ID", "Status", "Description", "Progress", "ASR", "Created"]
    rows = []
    
    for job in jobs:
        job_id = job.get('job_id', job.get('id', 'N/A'))
        desc = job.get('description', 'N/A')
        desc_display = desc[:30] + "..." if len(desc) > 30 else desc
        
        completed = job.get('completed_objectives', 0)
        total = job.get('total_objectives', 0)
        progress = f"{completed}/{total}" if total > 0 else "N/A"
        
        rows.append([
            str(job_id),
            format_status_plain(job.get('status', 'unknown')),
            desc_display,
            progress,
            f"{job.get('asr', 0):.1%}" if job.get('asr') is not None else 'N/A',
            format_datetime(job.get('created_at', ''))
        ])
    
    table = create_table(f"Found {len(jobs)} job(s)", headers, rows)
    console.print(table)

def show_job(client: APIClient, args):
    """Show job details"""
    job_id = select_job(client, getattr(args, 'job_id', None))
    if not job_id:
        return
    
    with console.status(f"[cyan]Fetching job {job_id}...[/cyan]"):
        data = client.get(f"/jobs/{job_id}")
    
    if not data:
        return
    
    if hasattr(args, 'json') and args.json:
        print_json(data, title=f"Job #{job_id}")
        return
    
    # Display job details
    job_id_display = data.get('job_id', data.get('id', 'N/A'))
    print_panel(f"Job #{job_id_display}", style="cyan")
    
    details = []
    details.append(f"Status: {format_status_plain(data.get('status', 'unknown'))}")
    details.append(f"Description: {data.get('description', 'N/A')}")
    details.append(f"Created: {format_datetime(data.get('created_at', ''))}")
    
    if data.get('completed_at'):
        details.append(f"Completed: {format_datetime(data['completed_at'])}")
    
    completed = data.get('completed_objectives', 0)
    total = data.get('total_objectives', 0)
    details.append(f"Progress: {completed}/{total}")
    
    if data.get('asr') is not None:
        details.append(f"Attack Success Rate: {data['asr']:.1%}")
    
    console.print("\n".join(details))

def show_results(client: APIClient, args):
    """Show job results with trajectories"""
    job_id = select_job(client, getattr(args, 'job_id', None))
    if not job_id:
        return
    
    with console.status(f"[cyan]Fetching results for job {job_id}...[/cyan]"):
        data = client.get(f"/jobs/{job_id}/results")
    
    if not data:
        return
    
    results = data.get('results', [])
    
    # Filter if requested
    if getattr(args, 'successful', False):
        results = [r for r in results if r.get('success')]
    elif getattr(args, 'failed', False):
        results = [r for r in results if not r.get('success')]
    
    if hasattr(args, 'json') and args.json:
        print_json({'job_id': job_id, 'results': results}, title=f"Results for Job #{job_id}")
        return
    
    # Display results
    if not results:
        print_warning("No results found")
        return
    
    print_panel(f"Results for Job #{job_id} - {len(results)} attack(s)", style="cyan")
    
    for idx, result in enumerate(results, 1):
        status = "[green]✓ Success[/green]" if result.get('success') else "[red]✗ Failed[/red]"
        console.print(f"\n[bold]Attack {idx}:[/bold] {status}")
        
        if result.get('objective'):
            console.print(f"  Objective: {result['objective'][:100]}...")
        if result.get('prompt'):
            console.print(f"  Prompt: {result['prompt'][:100]}...")
        if result.get('response'):
            console.print(f"  Response: {result['response'][:100]}...")
        if result.get('trajectory'):
            console.print(f"  Trajectory steps: {len(result['trajectory'])}")

def export_results(client: APIClient, args):
    """Export job results"""
    job_id = select_job(client, getattr(args, 'job_id', None))
    if not job_id:
        return
    
    with console.status(f"[cyan]Fetching results for job {job_id}...[/cyan]"):
        data = client.get(f"/jobs/{job_id}/results")
    
    if not data:
        return
    
    results = data.get('results', [])
    
    if not results:
        print_warning("No results to export")
        return
    
    # Export to CSV
    if getattr(args, 'csv', None):
        fieldnames = ['index', 'success', 'objective', 'prompt', 'response', 'trajectory_steps']
        
        csv_data = []
        for idx, result in enumerate(results, 1):
            csv_data.append({
                'index': idx,
                'success': result.get('success', False),
                'objective': result.get('objective', ''),
                'prompt': result.get('prompt', ''),
                'response': result.get('response', ''),
                'trajectory_steps': len(result.get('trajectory', []))
            })
        
        save_to_csv(csv_data, args.csv, fieldnames)
    
    # Export to JSON file
    elif getattr(args, 'json_file', None):
        output_file = Path(args.json_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({'job_id': job_id, 'results': results}, f, indent=2)
        
        print_success(f"Results exported to: {output_file.absolute()}")
    else:
        # Default: print JSON to stdout
        print_json({'job_id': job_id, 'results': results})

def attach_to_job(client: APIClient, args):
    """Attach to a running job and show live updates"""
    job_id = select_job(client, getattr(args, 'job_id', None))
    if not job_id:
        return
    
    interval = getattr(args, 'interval', 5)
    
    print_info(f"Attaching to job {job_id} (checking every {interval}s, Ctrl+C to stop)...")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            # Get initial job info
            initial_job = client.get(f"/jobs/{job_id}")
            if not initial_job:
                print_error(f"Job {job_id} not found")
                return
            
            total = initial_job.get('total_objectives', 0)
            completed = initial_job.get('completed_objectives', 0)
            
            task = progress.add_task(
                f"Monitoring job {job_id}...", 
                total=total if total > 0 else None,
                completed=completed
            )
            
            while True:
                data = client.get(f"/jobs/{job_id}")
                if not data:
                    break
                
                status = data.get('status', 'unknown')
                completed = data.get('completed_objectives', 0)
                total = data.get('total_objectives', 0)
                
                progress.update(
                    task, 
                    description=f"Job {job_id}: {format_status_plain(status)} ({completed}/{total})",
                    completed=completed
                )
                
                if status in ['completed', 'failed', 'error']:
                    progress.stop()
                    console.print(f"\nJob {job_id} {status}")
                    
                    if status == 'completed':
                        print_success(f"Job completed successfully! ASR: {data.get('asr', 0):.1%}")
                    else:
                        print_error(f"Job {status}")
                    break
                
                time.sleep(interval)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Detached from job[/yellow]")

def delete_job(client: APIClient, args):
    """Delete job(s)"""
    if getattr(args, 'all', False):
        if not getattr(args, 'force', False):
            if not confirm_action("Delete ALL jobs?"):
                print_info("Deletion cancelled")
                return
        
        # Delete all jobs
        response = client.get("/jobs")
        if not response:
            return
        
        jobs = response.get('jobs', [])
        deleted_count = 0
        
        with console.status("[cyan]Deleting jobs...[/cyan]"):
            for job in jobs:
                job_id = job.get('job_id', job.get('id'))
                if client.delete(f"/jobs/{job_id}"):
                    deleted_count += 1
        
        print_success(f"Deleted {deleted_count} job(s)")
    else:
        job_id = select_job(client, getattr(args, 'job_id', None))
        if not job_id:
            return
        
        if not getattr(args, 'force', False):
            if not confirm_action(f"Delete job {job_id}?"):
                print_info("Deletion cancelled")
                return
        
        if client.delete(f"/jobs/{job_id}"):
            print_success(f"Job {job_id} deleted")
        else:
            print_error(f"Failed to delete job {job_id}")

def run_job(client: APIClient, args):
    """Run a new job from config file"""
    config = load_yaml_config(args.config_file)
    if not config:
        return
    
    if getattr(args, 'dry_run', False):
        print_info("Dry run - configuration is valid")
        print_json(config, title="Configuration")
        return
    
    print_info(f"Starting job with config: {args.config_file}")
    
    # Prepare payload
    payload = {
        "description": config.get("description", ""),
        "config": config.get("config", {})
    }
    
    response = client.post("/run", payload)
    if not response:
        return
    
    job_id = response.get('job_id')
    print_success(f"Job {job_id} started successfully")
    
    # Display job info
    result_info = []
    result_info.append(f"[bold]Job ID:[/bold] {job_id}")
    result_info.append(f"[bold]Status:[/bold] {format_status_plain(response.get('status', 'unknown'))}")
    if response.get('dataset_used'):
        result_info.append(f"[bold]Dataset:[/bold] {response.get('dataset_used')}")
    if response.get('total_objectives'):
        result_info.append(f"[bold]Objectives:[/bold] {response.get('total_objectives')}")
    
    print_panel("\n".join(result_info), title="Job Submitted", style="green")
    
    if getattr(args, 'attach', False):
        args.job_id = job_id
        args.interval = 5
        attach_to_job(client, args)