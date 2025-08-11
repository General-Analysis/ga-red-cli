#!/usr/bin/env python3
"""
REDit Job Runner - Execute attack configurations via the REDit server API

Usage:
    python run_job.py <config_file>
    python run_job.py --help

Example:
    python run_job.py configs/tap_basic.yaml
"""

import yaml
import json
import requests
import sys
import argparse
import time
import csv
from pathlib import Path
import dotenv
import os
from datetime import datetime

# Load environment variables
dotenv.load_dotenv()

def print_usage():
    """Print usage information"""
    print(__doc__)

def run_job(config_path: str, monitor: bool = False):
    """
    Run a job from a configuration file
    
    Args:
        config_path: Path to the YAML configuration file
        monitor: If True, monitor job status until completion
    """
    # Convert to Path object
    config_file = Path(config_path)
    
    # Check if file exists
    if not config_file.exists():
        print(f"❌ Error: Configuration file '{config_path}' not found")
        sys.exit(1)
    
    # Read the configuration
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error reading configuration file: {e}")
        sys.exit(1)
    
    print("✅ Configuration loaded successfully!")
    print(f"📄 Config file: {config_file}")
    print(f"📝 Description: {config.get('description', 'N/A')}")
    
    if 'config' in config:
        if 'attack' in config['config']:
            print(f"⚔️  Attack type: {config['config']['attack'].get('type', 'N/A')}")
        if 'models' in config['config'] and 'target' in config['config']['models']:
            print(f"🎯 Target model: {config['config']['models']['target'].get('name', 'N/A')}")
    
    print("-" * 50)
    
    # Check for API key
    api_key = os.environ.get("GA_KEY")
    if not api_key:
        print("❌ Error: GA_KEY environment variable not set")
        print("Please set your API key: export GA_KEY=your_api_key")
        sys.exit(1)
    
    # Prepare the API request
    api_url = os.environ.get("REDIT_API_URL", "https://art-server.generalanalysis.com") + "/run"
    
    payload = {
        "description": config.get("description", ""),
        "config": config.get("config", {})
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    # Make the API call
    print(f"🚀 Sending request to REDit server at {api_url}...")
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to REDit server")
        print("Make sure the server is running and accessible")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error making request: {e}")
        sys.exit(1)
    
    # Check the response
    if response.status_code == 200:
        result = response.json()
        print("✅ Attack job created successfully!")
        print(json.dumps(result, indent=2))
        
        # If monitoring is enabled, track job status
        if monitor and 'job_id' in result:
            job_id = result['job_id']
            print("\n" + "=" * 50)
            print(f"📊 Monitoring job {job_id}...")
            print("=" * 50)
            
            while True:
                time.sleep(5)  # Wait 5 seconds between checks
                
                try:
                    base_url = os.environ.get("REDIT_API_URL", "https://art-server.generalanalysis.com")
                    status_url = f"{base_url}/jobs/{job_id}"
                    status_response = requests.get(status_url, headers=headers)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        current_time = datetime.now().strftime("%H:%M:%S")
                        status = status_data.get('status', 'unknown')
                        
                        print(f"[{current_time}] Status: {status}")
                        
                        # Check if job is complete
                        if status in ['completed', 'failed', 'error']:
                            print("\n" + "=" * 50)
                            if status == 'completed':
                                print("✅ Job completed successfully!")
                            else:
                                print(f"❌ Job ended with status: {status}")
                            print("Final job details:")
                            print(json.dumps(status_data, indent=2))
                            break
                            
                    else:
                        print(f"⚠️  Could not check status: {status_response.status_code}")
                        
                except KeyboardInterrupt:
                    print("\n⏹️  Monitoring stopped by user")
                    print(f"Job {job_id} is still running in the background")
                    break
                except Exception as e:
                    print(f"⚠️  Error checking status: {e}")
                    
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='REDit Job Runner - Execute attack configurations via the REDit server API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_job.py configs/tap_basic.yaml
  python run_job.py configs/tap_basic.yaml --monitor
  python run_job.py --help
        """
    )
    
    parser.add_argument(
        'config_file',
        help='Path to the YAML configuration file'
    )
    
    parser.add_argument(
        '--monitor', '-m',
        action='store_true',
        help='Monitor job status until completion (checks every 5 seconds)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the job
    run_job(args.config_file, monitor=args.monitor)

if __name__ == "__main__":
    main()
