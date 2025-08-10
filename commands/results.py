"""
Results command - Get and export job results
"""

import argparse
import json
from pathlib import Path
from typing import Optional
from utils import APIClient, save_to_csv, print_json, format_status

def add_parser(subparsers):
    """Add results command parser"""
    parser = subparsers.add_parser(
        'results',
        help='Get and export job results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Retrieve and export job results',
        epilog="""
Examples:
  ga-red results 123                        # View results for job 123
  ga-red results 123 --csv output.csv       # Export to CSV
  ga-red results 123 --json                 # Output as JSON
  ga-red results 123 --json > results.json  # Save JSON to file
        """
    )
    
    parser.add_argument(
        'job_id',
        type=int,
        help='Job ID to get results for'
    )
    
    parser.add_argument(
        '--csv', '-c',
        type=str,
        help='Export results to CSV file'
    )
    
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results as JSON'
    )
    
    parser.add_argument(
        '--summary', '-s',
        action='store_true',
        help='Show summary only'
    )
    
    parser.add_argument(
        '--successful', 
        action='store_true',
        help='Show only successful attacks'
    )
    
    parser.add_argument(
        '--failed',
        action='store_true',
        help='Show only failed attacks'
    )

def execute(args):
    """Execute results command"""
    client = APIClient()
    
    job_id = args.job_id
    
    # Fetch results
    print(f"Fetching results for job {job_id}...")
    data = client.get(f"/jobs/{job_id}/results")
    
    if not data:
        return
    
    job = data.get('job', {})
    results = data.get('results', [])
    
    if not results:
        print("Warning: No results found for this job")
        return
    
    # Filter results if requested
    if args.successful:
        results = [r for r in results if r.get('success')]
    elif args.failed:
        results = [r for r in results if not r.get('success')]
    
    # Export to CSV if requested
    if args.csv:
        export_to_csv(job, results, args.csv)
        return
    
    # Output as JSON if requested
    if args.json:
        output = {
            'job': job,
            'results': results
        }
        print_json(output)
        return
    
    # Display results
    if args.summary:
        display_summary(job, results)
    else:
        display_full_results(job, results)

def display_summary(job: dict, results: list):
    """Display results summary"""
    print("\n" + "=" * 60)
    print(f"Results Summary - Job #{job.get('id', 'N/A')}")
    print("=" * 60)
    
    print(f"📝 Description: {job.get('description', 'N/A')}")
    print(f"Status: {format_status(job.get('status', 'unknown'))}")
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r.get('success'))
    failed = total - successful
    
    print(f"\nStatistics:")
    print(f"  Total attacks: {total}")
    print(f"  Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"  Failed: {failed} ({failed/total*100:.1f}%)")
    
    if job.get('asr') is not None:
        print(f"  Overall ASR: {job.get('asr'):.1%}")
    
    # Show sample of successful attacks
    successful_results = [r for r in results if r.get('success')]
    if successful_results:
        print(f"\nSample Successful Attacks ({min(3, len(successful_results))}):")
        for i, result in enumerate(successful_results[:3], 1):
            print(f"\n  {i}. Objective: {result.get('objective', 'N/A')[:60]}...")
            if result.get('payload'):
                print(f"     Payload: {result.get('payload', '')[:60]}...")

def display_full_results(job: dict, results: list):
    """Display full results"""
    print("\n" + "=" * 60)
    print(f"Job Results - #{job.get('id', 'N/A')}")
    print("=" * 60)
    
    print(f"📝 Description: {job.get('description', 'N/A')}")
    print(f"Status: {format_status(job.get('status', 'unknown'))}")
    
    # Statistics
    total = len(results)
    successful = sum(1 for r in results if r.get('success'))
    
    print(f"\nStatistics:")
    print(f"  Total: {total} | Success: {successful} ({successful/total*100:.1f}%)")
    if job.get('asr') is not None:
        print(f"  ASR: {job.get('asr'):.1%}")
    
    print(f"\nIndividual Results ({total}):")
    print("-" * 60)
    
    for i, result in enumerate(results, 1):
        success_icon = "✅" if result.get('success') else "❌"
        print(f"\n{i}. {success_icon} Result #{i}")
        
        # Objective
        objective = result.get('objective', 'N/A')
        if len(objective) > 100:
            print(f"   Objective: {objective[:100]}...")
        else:
            print(f"   Objective: {objective}")
        
        # Payload
        if result.get('payload'):
            payload = result.get('payload', '')
            if len(payload) > 100:
                print(f"   Payload: {payload[:100]}...")
            else:
                print(f"   Payload: {payload}")
        
        # Output
        if result.get('output'):
            output = result.get('output', '')
            if len(output) > 100:
                print(f"   Output: {output[:100]}...")
            else:
                print(f"   Output: {output}")
        
        # Trajectory info
        trajectory = result.get('trajectory', [])
        if trajectory:
            print(f"   Trajectory: {len(trajectory)} step(s)")
        
        if i < total:
            print("   " + "-" * 40)

def export_to_csv(job: dict, results: list, output_path: str):
    """Export results to CSV file"""
    print(f"Preparing CSV export...")
    
    # Get job_id - handle both 'job_id' and 'id' field names
    job_id = job.get('job_id', job.get('id', ''))
    
    # Prepare data for CSV
    csv_data = []
    for result in results:
        trajectory = result.get('trajectory', [])
        trajectory_length = len(trajectory) if isinstance(trajectory, list) else 0
        # Convert trajectory to JSON string for CSV storage
        trajectory_json = json.dumps(trajectory) if trajectory else ''
        
        csv_data.append({
            'job_id': job_id,
            'job_description': job.get('description', ''),
            'job_status': job.get('status', ''),
            'job_asr': job.get('asr', ''),
            'objective': result.get('objective', ''),
            'success': result.get('success', False),
            'payload': result.get('payload', ''),
            'output': result.get('output', ''),
            'trajectory_length': trajectory_length,
            'trajectory': trajectory_json,
            'created_at': job.get('created_at', '')
        })
    
    # Define fieldnames
    fieldnames = [
        'job_id',
        'job_description',
        'job_status',
        'job_asr',
        'objective',
        'success',
        'payload',
        'output',
        'trajectory_length',
        'trajectory',
        'created_at'
    ]
    
    # Save to CSV
    if save_to_csv(csv_data, output_path, fieldnames):
        print(f"Exported {len(results)} results")
        
        # Print summary
        successful = sum(1 for r in results if r.get('success'))
        print(f"  Successful: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
