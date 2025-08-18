"""
Shared utilities for REDit CLI with Rich formatting
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import dotenv
import readchar

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Confirm
from rich import print as rprint
from rich.text import Text
from rich.json import JSON
from rich.live import Live
from rich.style import Style

# Load environment variables
dotenv.load_dotenv()

# Create global console instance
console = Console()

class APIClient:
    """Client for interacting with REDit server API"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        """Initialize API client
        
        Args:
            base_url: Base URL for the API (default: https://art-server.generalanalysis.com)
            api_key: API key for authentication (default: from GA_KEY env var)
        """
        self.base_url = base_url or os.environ.get("REDIT_API_URL", "https://art-server.generalanalysis.com")
        print(self.base_url)
        self.api_key = api_key or os.environ.get("GA_KEY")
        
        if not self.api_key:
            console.print("[yellow]Warning: GA_KEY environment variable not set[/yellow]")
            console.print("Set it with: [cyan]export GA_KEY=your_api_key[/cyan]")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
    
    def get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make GET request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                console.print(f"[red]Error: {response.status_code}[/red]")
                console.print(response.text)
                return None
        except requests.exceptions.ConnectionError:
            console.print(f"[red]Error: Could not connect to {self.base_url}[/red]")
            console.print("[yellow]Make sure the REDit server is running[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make POST request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=data, headers=self.headers)
            if response.status_code in [200, 201]:  # Accept both 200 and 201 for successful creation
                return response.json()
            else:
                console.print(f"[red]Error: {response.status_code}[/red]")
                console.print(response.text)
                return None
        except requests.exceptions.ConnectionError:
            console.print(f"[red]Error: Could not connect to {self.base_url}[/red]")
            console.print("[yellow]Make sure the REDit server is running[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None
    
    def delete(self, endpoint: str) -> bool:
        """Make DELETE request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.delete(url, headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return False

    def get_bytes(self, endpoint: str) -> Optional[bytes]:
        """GET request that returns raw bytes (for downloads)."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.content
            else:
                console.print(f"[red]Error: {response.status_code}[/red]")
                console.print(response.text)
                return None
        except requests.exceptions.ConnectionError:
            console.print(f"[red]Error: Could not connect to {self.base_url}[/red]")
            console.print("[yellow]Make sure the REDit server is running[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None

def format_datetime(dt_str: str) -> str:
    """Format ISO datetime string to readable format"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str

def format_status(status: str) -> Text:
    """Format status with color"""
    status_styles = {
        'pending': ('Pending', 'yellow'),
        'running': ('Running', 'cyan'),
        'completed': ('Completed', 'green'),
        'failed': ('Failed', 'red'),
        'error': ('Error', 'red')
    }
    
    text, color = status_styles.get(status, (status.title(), 'white'))
    return Text(text, style=color)

def format_status_plain(status: str) -> str:
    """Format status for display"""
    status_map = {
        'pending': 'Pending',
        'running': 'Running',
        'completed': 'Completed',
        'failed': 'Failed',
        'error': 'Error'
    }
    return status_map.get(status, status.title())

def print_json(data: Any, title: str = None):
    """Pretty print JSON data with Rich"""
    if title:
        console.print(Panel(JSON(json.dumps(data)), title=title, expand=False))
    else:
        console.print(JSON(json.dumps(data)))

def confirm_action(message: str) -> bool:
    """Ask user for confirmation using Rich prompt"""
    return Confirm.ask(message)

def load_yaml_config(file_path: str) -> Optional[Dict[str, Any]]:
    """Load YAML configuration file"""
    import yaml
    
    config_file = Path(file_path)
    if not config_file.exists():
        console.print(f"[red]Error: Configuration file '{file_path}' not found[/red]")
        return None
    
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error reading configuration file: {e}[/red]")
        return None

def save_to_csv(data: list, output_path: str, fieldnames: list):
    """Save data to CSV file"""
    import csv
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        console.print(f"[green]Data saved to: {output_file.absolute()}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]Error saving to CSV: {e}[/red]")
        return False

def create_table(title: str, headers: List[str], rows: List[List[Any]], 
                 show_header: bool = True, show_lines: bool = False) -> Table:
    """Create a Rich table with consistent styling"""
    table = Table(title=title, show_header=show_header, show_lines=show_lines)
    
    # Add columns with styling
    for header in headers:
        if header.lower() in ['id', 'job id']:
            table.add_column(header, style="cyan", no_wrap=True)
        elif header.lower() in ['status']:
            table.add_column(header, no_wrap=True)
        elif header.lower() in ['created', 'updated', 'created at', 'updated at']:
            table.add_column(header, style="dim")
        else:
            table.add_column(header)
    
    # Add rows
    for row in rows:
        # Convert all values to strings and handle None
        str_row = [str(val) if val is not None else "N/A" for val in row]
        table.add_row(*str_row)
    
    return table

def print_panel(content: str, title: str = None, style: str = None):
    """Print content in a styled panel"""
    console.print(Panel(content, title=title, style=style, expand=False))

def print_success(message: str):
    """Print success message"""
    console.print(f"[green]{message}[/green]")

def print_error(message: str):
    """Print error message"""
    console.print(f"[red]Error: {message}[/red]")

def print_warning(message: str):
    """Print warning message"""
    console.print(f"[yellow]Warning: {message}[/yellow]")

def print_info(message: str):
    """Print info message"""
    console.print(f"[cyan]{message}[/cyan]")

def print_yaml(data: Dict[str, Any], title: str = None):
    """Print YAML data with syntax highlighting"""
    import yaml
    yaml_str = yaml.dump(data, default_flow_style=False, sort_keys=False)
    syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
    if title:
        console.print(Panel(syntax, title=title, expand=False))
    else:
        console.print(syntax)

def create_progress_bar() -> Progress:
    """Create a progress bar for long-running operations"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    )

def interactive_select(
    items: List[Dict[str, Any]], 
    title: str = "Select an item",
    columns: List[Dict[str, str]] = None,
    id_field: str = 'id',
    allow_none: bool = True
) -> Optional[Any]:
    """
    Interactive selection from a list of items using arrow keys.
    
    Args:
        items: List of dictionaries containing the items
        title: Title for the selection table
        columns: List of column definitions [{"key": "field_name", "header": "Display Name", "style": "cyan"}]
        id_field: Field to return when item is selected
        allow_none: Whether to allow cancelling selection (returns None)
    
    Returns:
        Selected item's id_field value or None if cancelled
    """
    if not items:
        console.print("[yellow]No items available for selection[/yellow]")
        return None
    
    if columns is None:
        # Default columns if not specified
        columns = [{"key": id_field, "header": "ID", "style": "cyan"}]
    
    selected_index = 0
    
    def render_table(selected_idx):
        table = Table(
            title=f"{title} - Use ↑↓ arrows to navigate, Enter to select" + 
                  (", Ctrl+C to cancel" if allow_none else ""),
            show_header=True, 
            header_style="bold cyan"
        )
        
        # Add columns
        for col in columns:
            table.add_column(
                col.get("header", col["key"]), 
                style=col.get("style", "white"),
                no_wrap=col.get("no_wrap", False),
                width=col.get("width"),
                max_width=col.get("max_width"),
                overflow=col.get("overflow", "fold")
            )
        
        # Add rows with selection highlighting
        for idx, item in enumerate(items):
            row_style = Style(bgcolor="blue", bold=True) if idx == selected_idx else Style()
            row_data = []
            
            for col in columns:
                value = item.get(col["key"], "N/A")
                # Apply any custom formatting
                if "formatter" in col and callable(col["formatter"]):
                    value = col["formatter"](value)
                else:
                    value = str(value) if value is not None else "N/A"
                row_data.append(value)
            
            table.add_row(*row_data, style=row_style)
        
        return table
    
    try:
        with Live(render_table(selected_index), console=console, auto_refresh=False) as live:
            while True:
                try:
                    key = readchar.readkey()
                    
                    if key == readchar.key.UP:
                        selected_index = (selected_index - 1) % len(items)
                        live.update(render_table(selected_index), refresh=True)
                    elif key == readchar.key.DOWN:
                        selected_index = (selected_index + 1) % len(items)
                        live.update(render_table(selected_index), refresh=True)
                    elif key == readchar.key.ENTER or key == '\r' or key == '\n':
                        selected_item = items[selected_index]
                        return selected_item.get(id_field)
                    elif allow_none and (key == readchar.key.CTRL_C or key == '\x03'):
                        return None
                        
                except KeyboardInterrupt:
                    if allow_none:
                        return None
                    continue
                    
    except KeyboardInterrupt:
        if allow_none:
            console.print("\n[yellow]Selection cancelled[/yellow]")
            return None
        raise
    except Exception as e:
        console.print(f"[red]Error in selection: {e}[/red]")
        return None

def select_job(client: APIClient, job_id: Optional[int] = None) -> Optional[int]:
    """
    Select a job interactively or return the provided job_id.
    
    Args:
        client: API client instance
        job_id: Optional job ID. If None, shows interactive selection
    
    Returns:
        Selected or provided job ID, or None if cancelled
    """
    if job_id is not None:
        return job_id
    
    console.print("[cyan]Fetching available jobs...[/cyan]")
    response = client.get("/jobs")
    if not response:
        return None
    
    jobs = response.get('jobs', [])
    if not jobs:
        console.print("[yellow]No jobs found[/yellow]")
        return None
    
    # Build dataset id -> name map for labeling
    ds_map = {}
    try:
        ds_resp = client.get("/datasets")
        ds_list = ds_resp if isinstance(ds_resp, list) else (ds_resp.get('datasets', []) if ds_resp else [])
        for ds in ds_list:
            ds_map[ds.get('id')] = ds.get('name')
    except Exception:
        pass
    
    columns = [
        {"key": "job_id", "header": "Job ID", "style": "cyan", "no_wrap": True, "width": 8},
        {"key": "status", "header": "Status", "formatter": format_status_plain, "no_wrap": True, "width": 10},
        {"key": "algorithm", "header": "Algorithm", "no_wrap": True, "width": 14},
        {"key": "target", "header": "Target", "no_wrap": True, "width": 20},
        {"key": "dataset", "header": "Dataset", "no_wrap": True, "width": 20},
        {"key": "progress", "header": "Progress", "no_wrap": True, "width": 10,
         "formatter": lambda j: f"{j.get('completed_objectives', 0)}/{j.get('total_objectives', 0)}"},
        {"key": "description", "header": "Description", "max_width": 50, "overflow": "ellipsis"}
    ]
    
    # Transform job data to include calculated fields
    for job in jobs:
        cfg = job.get('config') or {}
        attack_cfg = cfg.get('attack') or {}
        target_cfg = cfg.get('target') or {}
        # Fallback for legacy configs
        if not target_cfg and (cfg.get('models') or {}).get('target'):
            target_cfg = (cfg.get('models') or {}).get('target')
        dataset_label = None
        if cfg.get('dataset_id') is not None:
            ds_id = cfg.get('dataset_id')
            dataset_label = ds_map.get(ds_id, f"id:{ds_id}")
        elif cfg.get('objectives'):
            dataset_label = "custom_objectives"
        job['algorithm'] = attack_cfg.get('type') or 'N/A'
        job['target'] = target_cfg.get('name') or 'N/A'
        job['dataset'] = dataset_label or 'N/A'
        job['progress'] = job  # Pass the whole job object for the formatter
    
    return interactive_select(jobs, "Select a Job", columns, id_field="job_id")

def select_dataset(client: APIClient, dataset_name: Optional[str] = None) -> Optional[int]:
    """
    Select a dataset interactively or resolve provided name/id to dataset_id.
    
    Args:
        client: API client instance
        dataset_name: Optional dataset name or id (as string). If None, shows interactive selection.
    
    Returns:
        Selected dataset id, or None if cancelled/not found.
    """
    # If user provided a value, try to interpret as ID first, then resolve by name
    if dataset_name is not None:
        # Try numeric id
        try:
            return int(str(dataset_name).strip())
        except Exception:
            pass
        # Resolve by name lookup
        response = client.get("/datasets")
        if not response:
            return None
        datasets = response if isinstance(response, list) else response.get('datasets', [])
        for ds in datasets:
            if str(ds.get('name', '')).lower() == str(dataset_name).lower():
                return ds.get('id')
        console.print(f"[yellow]Dataset '{dataset_name}' not found[/yellow]")
        return None
    
    # Interactive selection
    console.print("[cyan]Fetching available datasets...[/cyan]")
    response = client.get("/datasets")
    if not response:
        return None
    
    datasets = response if isinstance(response, list) else response.get('datasets', [])
    if not datasets:
        console.print("[yellow]No datasets found[/yellow]")
        return None
    
    columns = [
        {"key": "name", "header": "Dataset Name", "style": "cyan", "no_wrap": True},
        {"key": "size", "header": "Entries", "no_wrap": True, "width": 10},
        {"key": "description", "header": "Description", "max_width": 50, "overflow": "ellipsis"},
        {"key": "created_at", "header": "Created", "formatter": format_datetime, "no_wrap": True}
    ]
    
    return interactive_select(datasets, "Select a Dataset", columns, id_field="id")

def transform_config_for_api(raw_config: Dict[str, Any], client: APIClient) -> Dict[str, Any]:
    """
    Transform legacy CLI config into the server's expected JobRequest format.
    - Move models.target -> target { name, system_prompt }
    - Resolve dataset name -> dataset_id
    - Preserve attack and objectives as-is
    """
    import copy
    config = copy.deepcopy(raw_config or {})
    payload = config.get("config", {})
    
    # Map models.target -> target
    if "target" not in payload:
        models = payload.get("models") or {}
        target_model = models.get("target") or {}
        if target_model:
            payload["target"] = {
                "name": target_model.get("name"),
                "system_prompt": payload.get("target", {}).get("system_prompt", "You are a helpful AI assistant.")
            }
    
    # Resolve dataset name -> dataset_id
    if "dataset_id" not in payload and isinstance(payload.get("dataset"), str):
        try:
            datasets = client.get("/datasets")
            all_ds = datasets if isinstance(datasets, list) else (datasets.get('datasets', []) if datasets else [])
            match = next((d for d in all_ds if str(d.get('name', '')).lower() == payload["dataset"].lower()), None)
            if match and match.get('id') is not None:
                payload["dataset_id"] = match['id']
                # Remove legacy field to avoid server-side conflict
                del payload["dataset"]
        except Exception:
            # Leave as-is; server will error clearly
            pass
    
    # Remove models block if not needed
    if "models" in payload and "target" in payload:
        try:
            del payload["models"]
        except Exception:
            pass
    
    config["config"] = payload
    return config

def select_algorithm(client: APIClient, algorithm_name: Optional[str] = None) -> Optional[str]:
    """
    Select an algorithm interactively or return the provided algorithm_name.
    
    Args:
        client: API client instance
        algorithm_name: Optional algorithm name. If None, shows interactive selection
    
    Returns:
        Selected or provided algorithm name, or None if cancelled
    """
    if algorithm_name is not None:
        return algorithm_name
    
    console.print("[cyan]Fetching available algorithms...[/cyan]")
    response = client.get("/algorithms")
    if not response:
        return None
    
    algorithms = response if isinstance(response, list) else response.get('algorithms', [])
    if not algorithms:
        console.print("[yellow]No algorithms found[/yellow]")
        return None
    
    columns = [
        {"key": "name", "header": "Algorithm", "style": "cyan", "no_wrap": True},
        {"key": "description", "header": "Description", "max_width": 60, "overflow": "ellipsis"}
    ]
    
    return interactive_select(algorithms, "Select an Algorithm", columns, id_field="name")
