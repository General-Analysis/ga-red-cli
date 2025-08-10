"""
Jobs command - List, view, and delete jobs with Rich formatting
"""

import sys
import argparse
import time
from datetime import datetime
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, BarColumn, TaskProgressColumn
from typing import Optional
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from utils import (
    APIClient, format_datetime, format_status_plain, print_json, 
    confirm_action, create_table, console, print_success, print_error,
    print_warning, print_info, print_panel
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
    
    table.add_row("list", "List all jobs")
    table.add_row("get", "Get job details")
    table.add_row("delete", "Delete job(s)")
    table.add_row("status", "Get job status")
    table.add_row("attach", "Attach to a running job")
    
    console.print(table)
    
    console.print("\n[dim]For help on a specific action:[/dim]")
    console.print("  ga-red jobs [cyan]<action>[/cyan] --help")
    console.print()

def add_parser(subparsers):
    """Add jobs command parser"""
    parser = subparsers.add_parser(
        'jobs',
        help='Manage jobs (list, view, delete)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Manage REDit jobs',
        add_help=False  # We'll handle help ourselves
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
    list_parser = subparsers.add_parser('list', help='List all jobs')
    list_parser.add_argument(
        '--limit', '-l',
        type=int,
        help='Limit number of jobs to display'
    )
    list_parser.add_argument(
        '--status', '-s',
        choices=['pending', 'running', 'completed', 'failed', 'error'],
        help='Filter by status'
    )
    list_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get job details')
    get_parser.add_argument('job_id', type=int, help='Job ID')
    get_parser.add_argument(
        '--results', '-r',
        action='store_true',
        help='Include results'
    )
    get_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete job(s)')
    delete_parser.add_argument(
        'job_id',
        type=int,
        nargs='?',
        help='Job ID to delete'
    )
    delete_parser.add_argument(
        '--all',
        action='store_true',
        help='Delete all jobs'
    )
    delete_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Skip confirmation'
    )
    
    # Attach command
    attach_parser = subparsers.add_parser("attach", help="Attach to a running job")
    attach_parser.add_argument("job_id", type=int, help="Job ID to attach to")
    attach_parser.add_argument(
        "--interval", "-i",
        type=int,
        default=5,
        help="Status check interval in seconds (default: 5)"
    )
    # Status command
    status_parser = subparsers.add_parser('status', help='Get job status')
    status_parser.add_argument('job_id', type=int, help='Job ID')

def execute(args):
    """Execute jobs command"""
    # Check if help was requested
    if hasattr(args, 'help') and args.help:
        print_jobs_help()
        return
        
    client = APIClient()
    
    if not args.action:
        print_jobs_help()
        return
    
    if args.action == 'list':
        list_jobs(client, args)
    elif args.action == 'get':
        get_job(client, args)
    elif args.action == 'delete':
        delete_job(client, args)
    elif args.action == 'status':
        get_job_status(client, args)
    elif args.action == 'attach':
        attach_to_job(client, args)

def list_jobs(client: APIClient, args):
    """List all jobs"""
    with console.status("[cyan]Fetching jobs...[/cyan]"):
        response = client.get("/jobs")
    
    if not response:
        return
    
    # Extract jobs list from response dictionary
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
        # Handle both 'job_id' and 'id' field names
        job_id = job.get('job_id', job.get('id', 'N/A'))
        desc = job.get('description', 'N/A')
        desc_display = desc[:30] + "..." if len(desc) > 30 else desc
        
        # Progress display
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
    
    # Print summary
    status_counts = {}
    for job in jobs:
        status = job.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    summary_lines = []
    for status, count in status_counts.items():
        summary_lines.append(f"{format_status_plain(status)}: {count}")
    
    if summary_lines:
        print_panel("\n".join(summary_lines), title="Summary", style="cyan")

def get_job(client: APIClient, args):
    """Get job details"""
    job_id = args.job_id
    
    with console.status(f"[cyan]Fetching job {job_id}...[/cyan]"):
        # Determine endpoint
        endpoint = f"/jobs/{job_id}/results" if args.results else f"/jobs/{job_id}"
        data = client.get(endpoint)
    
    if not data:
        return
    
    # Output as JSON if requested
    if hasattr(args, 'json') and args.json:
        print_json(data, title=f"Job #{job_id}")
        return
    
    # Pretty print job details
    if args.results:
        job = data.get('job', {})
        results = data.get('results', [])
    else:
        job = data
        results = []
    
    # Handle both 'job_id' and 'id' field names
    display_id = job.get('job_id', job.get('id', 'N/A'))
    
    # Progress information
    completed = job.get('completed_objectives', 0)
    total = job.get('total_objectives', len(job.get('objectives', [])))
    
    # Create job info panel
    info_lines = []
    info_lines.append(f"[bold]Description:[/bold] {job.get('description', 'N/A')}")
    info_lines.append(f"[bold]Status:[/bold] {format_status_plain(job.get('status', 'unknown'))}")
    info_lines.append(f"[bold]Progress:[/bold] {completed}/{total} objectives completed")
    info_lines.append(f"[bold]ASR:[/bold] {job.get('asr', 0):.1%}" if job.get('asr') is not None else "[bold]ASR:[/bold] N/A")
    info_lines.append(f"[bold]Created:[/bold] {format_datetime(job.get('created_at', ''))}")
    info_lines.append(f"[bold]Updated:[/bold] {format_datetime(job.get('updated_at', ''))}")
    
    print_panel("\n".join(info_lines), title=f"Job #{display_id}", style="cyan")
    
    # Print objectives
    objectives = job.get('objectives', [])
    if objectives:
        console.print(f"\n[bold cyan]Objectives ({len(objectives)} total):[/bold cyan]")
        for i, obj in enumerate(objectives[:5], 1):
            console.print(f"  {i}. {obj[:80]}...")
        if len(objectives) > 5:
            console.print(f"  [dim]... and {len(objectives) - 5} more[/dim]")
    
    # Print results if included
    if results:
        successful = sum(1 for r in results if r.get('success'))
        
        # Results summary
        summary_lines = []
        summary_lines.append(f"[bold]Total Results:[/bold] {len(results)}")
        summary_lines.append(f"[bold green]Successful:[/bold green] {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
        summary_lines.append(f"[bold red]Failed:[/bold red] {len(results) - successful}/{len(results)} ({(len(results) - successful)/len(results)*100:.1f}%)")
        
        print_panel("\n".join(summary_lines), title="Results Summary", style="green")
        
        # Show sample results
        if results:
            console.print("\n[bold cyan]Recent results:[/bold cyan]")
            for i, result in enumerate(results[:3], 1):
                success_status = "[green]Success[/green]" if result.get('success') else "[red]Failed[/red]"
                console.print(f"\n  [bold]Result {i}:[/bold] {success_status}")
                console.print(f"    [dim]Objective:[/dim] {result.get('objective', 'N/A')[:60]}...")
                if result.get('payload'):
                    console.print(f"    [dim]Payload:[/dim] {result.get('payload', '')[:60]}...")

def get_job_status(client: APIClient, args):
    """Get quick job status"""
    job_id = args.job_id
    
    with console.status(f"[cyan]Checking status for job {job_id}...[/cyan]"):
        job = client.get(f"/jobs/{job_id}")
    
    if not job:
        return
    
    status = job.get('status', 'unknown')
    completed = job.get('completed_objectives', 0)
    total = job.get('total_objectives', 0)
    
    # Create status panel
    status_lines = []
    status_lines.append(f"[bold]Status:[/bold] {format_status_plain(status)}")
    status_lines.append(f"[bold]Progress:[/bold] {completed}/{total} objectives")
    if job.get('asr') is not None:
        status_lines.append(f"[bold]ASR:[/bold] {job.get('asr'):.1%}")
    
    print_panel("\n".join(status_lines), title=f"Job #{job_id}", style="cyan")

def delete_job(client: APIClient, args):
    """Delete job(s)"""
    if args.all:
        # Delete all jobs
        if not args.force:
            if not confirm_action("[red]Are you sure you want to delete ALL jobs?[/red]"):
                print_warning("Cancelled")
                return
        
        with console.status("[red]Deleting all jobs...[/red]"):
            success = client.delete("/jobs")
        
        if success:
            print_success("All jobs deleted successfully")
        else:
            print_error("Failed to delete jobs")
    
    elif args.job_id:
        # Delete specific job
        job_id = args.job_id
        
        if not args.force:
            if not confirm_action(f"[yellow]Are you sure you want to delete job #{job_id}?[/yellow]"):
                print_warning("Cancelled")
                return
        
        with console.status(f"[red]Deleting job {job_id}...[/red]"):
            success = client.delete(f"/jobs/{job_id}")
        
        if success:
            print_success(f"Job #{job_id} deleted successfully")
        else:
            print_error(f"Failed to delete job #{job_id}")
    
    else:
        print_error("Please specify a job ID or use --all flag")
        print_info("Use 'ga-red jobs delete --help' for more information")

def attach_to_job(client: APIClient, args):
    """Attach to a running job and monitor its progress"""
    job_id = args.job_id
    interval = args.interval
    
    # Get initial job info
    initial_job = client.get(f"/jobs/{job_id}")
    if not initial_job:
        print_error(f"Job {job_id} not found")
        return
    
    # Check if job is already completed
    status = initial_job.get('status', 'unknown')
    if status in ['completed', 'failed', 'error']:
        print_warning(f"Job {job_id} is already {status}")
        get_job_status(client, args)
        return
    
    console.print(f"\n[bold cyan]Attaching to job {job_id}[/bold cyan]")
    console.print(f"[dim]Checking every {interval} seconds[/dim]")
    console.print("[dim]Press Ctrl+C to detach[/dim]\n")
    
    # Create progress display with a proper progress bar
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    )
    
    try:
        with progress:
            total_objectives = initial_job.get('total_objectives', 0)
            completed_objectives = initial_job.get('completed_objectives', 0)
            
            # Create task with total if known
            if total_objectives > 0:
                task = progress.add_task(
                    f"[cyan]Processing objectives...",
                    total=total_objectives,
                    completed=completed_objectives
                )
            else:
                task = progress.add_task(
                    "[cyan]Processing...",
                    total=None
                )
            
            while True:
                time.sleep(interval)
                
                # Get job status
                job = client.get(f"/jobs/{job_id}")
                if not job:
                    print_warning("Failed to get job status")
                    break
                
                status = job.get('status', 'unknown')
                completed_objectives = job.get('completed_objectives', 0)
                total_objectives = job.get('total_objectives', 0)
                
                # Update progress bar
                if total_objectives > 0:
                    progress.update(
                        task, 
                        completed=completed_objectives,
                        description=f"[cyan]Status: {format_status_plain(status)} [{completed_objectives}/{total_objectives}]"
                    )
                else:
                    progress.update(
                        task,
                        description=f"[cyan]Status: {format_status_plain(status)}"
                    )
                
                # Check if complete
                if status in ['completed', 'failed', 'error']:
                    progress.stop()
                    
                    if status == 'completed':
                        result_info = []
                        result_info.append(f"[bold green]Job completed successfully[/bold green]")
                        result_info.append(f"[bold]Objectives completed:[/bold] {completed_objectives}/{total_objectives}")
                        if job.get('asr') is not None:
                            result_info.append(f"[bold]Final ASR:[/bold] {job.get('asr'):.1%}")
                        result_info.append(f"[bold]Started:[/bold] {format_datetime(job.get('created_at', 'N/A'))}")
                        result_info.append(f"[bold]Ended:[/bold] {format_datetime(job.get('updated_at', 'N/A'))}")
                        
                        print_panel("\n".join(result_info), title="Job Complete", style="green")
                    else:
                        print_error(f"Job ended with status: {status}")
                        console.print(f"[dim]Started: {job.get('created_at', 'N/A')}[/dim]")
                        console.print(f"[dim]Ended: {job.get('updated_at', 'N/A')}[/dim]")
                    break
                    
    except KeyboardInterrupt:
        console.print("\n[yellow]Detached from job[/yellow]")
        console.print(f"Job {job_id} is still running in the background")
        console.print(f"[dim]Use 'ga-red jobs attach {job_id}' to re-attach[/dim]")
        console.print(f"[dim]Use 'ga-red jobs status {job_id}' to check status[/dim]")
