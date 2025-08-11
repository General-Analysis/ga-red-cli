"""
Run command - Execute attack configurations with Rich formatting
"""

import argparse
import time
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, BarColumn, TaskProgressColumn
from utils import (
    APIClient, load_yaml_config, format_status_plain, print_json,
    console, print_success, print_error, print_warning, print_info,
    print_panel, print_yaml
)
import sys

def print_run_help():
    """Print run command help using Rich"""
    console.print(Panel.fit(
        "[bold red]Run Command[/bold red] - Execute attack configurations",
        title="Run Attack",
        border_style="red"
    ))
    
    console.print("\n[bold]Usage:[/bold]")
    console.print("  ga-red run [red]<config_file>[/red] [dim][options][/dim]\n")
    
    console.print("[bold]Options:[/bold]")
    console.print("  --monitor, -m     Monitor job status until completion")
    console.print("  --interval, -i    Status check interval in seconds (default: 5)")
    console.print("  --wait, -w        Wait for job completion without monitoring")
    console.print("  --json            Output job info as JSON")
    console.print()

def add_parser(subparsers):
    """Add run command parser"""
    parser = subparsers.add_parser(
        'run',
        help='Run attack from configuration file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Execute attack configurations',
        add_help=False
    )
    
    # Check if user is asking for help
    if len(sys.argv) >= 3 and sys.argv[1] == "run" and sys.argv[2] in ["--help", "-h"]:
        print_run_help()
        sys.exit(0)
    
    parser.add_argument(
        'config_file',
        help='Path to YAML configuration file'
    )
    
    parser.add_argument(
        '--monitor', '-m',
        action='store_true',
        help='Monitor job status until completion'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=5,
        help='Status check interval in seconds (default: 5)'
    )
    
    parser.add_argument(
        '--wait', '-w',
        action='store_true',
        help='Wait for job completion without monitoring'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output job info as JSON'
    )

def execute(args):
    """Execute run command"""
    client = APIClient()
    
    # Load configuration
    with console.status("[red]Loading configuration...[/red]"):
        config = load_yaml_config(args.config_file)
    
    if not config:
        return
    
    # Display config info
    config_info = []
    config_info.append(f"[bold]File:[/bold] {Path(args.config_file).absolute()}")
    config_info.append(f"[bold]Description:[/bold] {config.get('description', 'N/A')}")
    
    if 'config' in config:
        if 'attack' in config['config']:
            config_info.append(f"[bold]Attack type:[/bold] {config['config']['attack'].get('type', 'N/A')}")
        if 'models' in config['config'] and 'target' in config['config']['models']:
            config_info.append(f"[bold]Target model:[/bold] {config['config']['models']['target'].get('name', 'N/A')}")
    
    print_panel("\n".join(config_info), title="Configuration Loaded", style="red")
    
    # Prepare payload
    payload = {
        "description": config.get("description", ""),
        "config": config.get("config", {})
    }
    
    # Submit job
    console.print("\n[red]Submitting job to server...[/red]")
    result = client.post("/run", payload)
    
    if not result:
        return
    
    job_id = result.get('job_id')
    
    # Display result
    if args.json:
        print_json(result, title="Job Created")
    else:
        result_info = []
        result_info.append(f"[bold green]Job created successfully[/bold green]")
        result_info.append(f"[bold]Job ID:[/bold] {job_id}")
        result_info.append(f"[bold]Status:[/bold] {format_status_plain(result.get('status', 'unknown'))}")
        if result.get('dataset_used'):
            result_info.append(f"[bold]Dataset:[/bold] {result.get('dataset_used')}")
        if result.get('total_objectives'):
            result_info.append(f"[bold]Objectives:[/bold] {result.get('total_objectives')}")
        
        print_panel("\n".join(result_info), title="Job Submitted", style="green")
    
    # Monitor or wait if requested
    if args.monitor:
        monitor_job(client, job_id, args.interval)
    elif args.wait:
        wait_for_job(client, job_id, args.interval)

def monitor_job(client: APIClient, job_id: int, interval: int):
    """Monitor job status until completion with rich display"""
    console.print(f"\n[bold red]Monitoring job {job_id}[/bold red]")
    console.print(f"[dim]Checking every {interval} seconds[/dim]")
    console.print("[dim]Press Ctrl+C to stop monitoring[/dim]\n")
    
    # Create progress display with a proper progress bar
    progress = Progress(
        SpinnerColumn(style="red"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    )
    
    try:
        with progress:
            # Get initial job info to set up progress
            initial_job = client.get(f"/jobs/{job_id}")
            if not initial_job:
                print_warning("Failed to get initial job status")
                return
            
            total_objectives = initial_job.get('total_objectives', 0)
            
            # Create task with total if known
            if total_objectives > 0:
                task = progress.add_task(
                    f"[red]Processing objectives...",
                    total=total_objectives
                )
            else:
                task = progress.add_task(
                    "[red]Processing...",
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
                        description=f"[red]Status: {format_status_plain(status)} [{completed_objectives}/{total_objectives}]"
                    )
                else:
                    progress.update(
                        task,
                        description=f"[red]Status: {format_status_plain(status)}"
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
        console.print("\n[yellow]Monitoring stopped[/yellow]")
        console.print(f"Job {job_id} is still running in the background")
        console.print(f"[dim]Use 'ga-red jobs get {job_id}' to check status[/dim]")

def wait_for_job(client: APIClient, job_id: int, interval: int):
    """Wait for job completion with progress tracking"""
    
    # Get initial job info
    initial_job = client.get(f"/jobs/{job_id}")
    if not initial_job:
        print_warning("Failed to get job status")
        return
    
    total_objectives = initial_job.get('total_objectives', 0)
    
    # Create progress bar
    progress = Progress(
        SpinnerColumn(style="red"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )
    
    with progress:
        if total_objectives > 0:
            task = progress.add_task(
                f"[red]Waiting for job {job_id}...",
                total=total_objectives
            )
        else:
            task = progress.add_task(
                f"[red]Waiting for job {job_id}...",
                total=None
            )
        
        try:
            while True:
                time.sleep(interval)
                
                # Get job status
                job = client.get(f"/jobs/{job_id}")
                if not job:
                    print_warning("Failed to get job status")
                    break
                
                job_status = job.get('status', 'unknown')
                completed_objectives = job.get('completed_objectives', 0)
                
                # Update progress
                if total_objectives > 0:
                    progress.update(task, completed=completed_objectives)
                
                # Check if complete
                if job_status in ['completed', 'failed', 'error']:
                    if job_status == 'completed':
                        print_success(f"Job {job_id} completed successfully")
                        if job.get('asr') is not None:
                            console.print(f"[bold]ASR:[/bold] {job.get('asr'):.1%}")
                    else:
                        print_error(f"Job {job_id} ended with status: {job_status}")
                    break
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Wait cancelled[/yellow]")
            console.print(f"Job {job_id} is still running in the background")

def format_datetime(dt_str: str) -> str:
    """Format ISO datetime string to readable format"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str

# Fix missing import
