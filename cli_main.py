#!/usr/bin/env python3
"""
REDit CLI - Command-line interface for REDit server
Main entry point for the ga-red command
"""

import sys
import os
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add the CLI directory to Python path for imports
cli_dir = Path(__file__).parent
sys.path.insert(0, str(cli_dir))

# Import commands
import commands.jobs as jobs
import commands.run as run
import commands.results as results
import commands.config as config
import commands.algorithms as algorithms
import commands.datasets as datasets

console = Console()

def print_main_help():
    """Print main help using Rich formatting"""
    console.print(Panel.fit(
        "[bold cyan]REDit CLI[/bold cyan] - Manage and execute adversarial attacks",
        title="REDit Command Line Interface",
        border_style="cyan"
    ))
    
    console.print("\n[bold]Usage:[/bold]")
    console.print("  ga-red [cyan]<command>[/cyan] [dim][options][/dim]")
    console.print("  ga-red --help\n")
    
    # Create commands table
    table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    
    table.add_row("algorithms", "List and view available attack algorithms")
    table.add_row("datasets", "Manage datasets and their entries")
    table.add_row("jobs", "Manage jobs (list, view, delete)")
    table.add_row("run", "Run attack from configuration file")
    table.add_row("results", "Get and export job results")
    table.add_row("config", "Manage and validate configurations")
    
    console.print(table)
    
    console.print("\n[dim]For help on a specific command:[/dim]")
    console.print("  ga-red [cyan]<command>[/cyan] --help")
    console.print()

def main():
    """Main CLI entry point"""
    # Check if asking for help
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['--help', '-h']):
        print_main_help()
        sys.exit(0)
    
    parser = argparse.ArgumentParser(
        prog='ga-red',
        description='REDit CLI - Manage and execute adversarial attacks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False  # We'll handle help ourselves
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        title='Commands',
        description='Available commands',
        dest='command',
        help='Command to execute'
    )
    
    # Add command parsers
    algorithms.add_parser(subparsers)
    datasets.add_parser(subparsers)
    jobs.add_parser(subparsers)
    run.add_parser(subparsers)
    results.add_parser(subparsers)
    config.add_parser(subparsers)
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command specified, show help
    if not args.command:
        print_main_help()
        sys.exit(0)
    
    # Execute the appropriate command
    if args.command == 'algorithms':
        algorithms.execute(args)
    elif args.command == 'datasets':
        datasets.execute(args)
    elif args.command == 'jobs':
        jobs.execute(args)
    elif args.command == 'run':
        run.execute(args)
    elif args.command == 'results':
        results.execute(args)
    elif args.command == 'config':
        config.execute(args)
    else:
        console.print(f"[red]Unknown command: {args.command}[/red]")
        print_main_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
