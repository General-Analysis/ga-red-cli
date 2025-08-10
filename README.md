# REDit CLI

A beautiful command-line interface for managing and executing adversarial attacks using the REDit server, featuring Rich terminal formatting for enhanced readability.

## Features

- 🎨 Beautiful terminal output with Rich formatting
- 📊 Colored tables and progress indicators
- 🔄 Real-time job monitoring with progress bars
- 📈 Formatted status displays and panels
- 🎯 Syntax highlighting for configurations

## Installation

### Quick Install (Recommended)

1. Navigate to the CLI directory:
   ```bash
   cd cli
   ```

2. Run the installation script:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

   Or install manually with pip:
   ```bash
   pip install -e .
   ```

3. The `ga-red` command will now be available globally in your terminal!

### Setup

1. Make sure you have the REDit server running at `http://localhost:8000`
2. Set your API key:
   ```bash
   export GA_KEY=your_api_key
   ```

## Usage

After installation, you can use `ga-red` from anywhere:
```bash
ga-red <command> [options]
```

No need to navigate to the CLI directory or use `ga-red`!

## Available Commands

### 1. Jobs Management

```bash
# List all jobs (with beautiful table output)
ga-red jobs list

# List last 5 jobs
ga-red jobs list --limit 5

# Filter by status
ga-red jobs list --status completed

# Get job details (formatted panels)
ga-red jobs get 123

# Get job with results
ga-red jobs get 123 --results

# Check job status
ga-red jobs status 123

# Delete a job
ga-red jobs delete 123

# Delete all jobs

# Attach to a running job (monitor progress)
ga-red jobs attach 123

# Attach with custom interval
ga-red jobs attach 123 --interval 10
ga-red jobs delete --all
```

### 2. Run Attacks

```bash
# Run attack from config file
ga-red run configs/tap_basic.yaml

# Run and monitor status (with progress bar)
ga-red run configs/tap_basic.yaml --monitor

# Run with custom check interval
ga-red run configs/tap_basic.yaml --monitor --interval 10

# Run and wait for completion
ga-red run configs/tap_basic.yaml --wait
```

### 3. Get Results

```bash
# View results for a job
ga-red results 123

# Export results to CSV
ga-red results 123 --csv output.csv

# Output results as JSON (with syntax highlighting)
ga-red results 123 --json

# Show summary only
ga-red results 123 --summary

# Filter successful attacks
ga-red results 123 --successful

# Filter failed attacks
ga-red results 123 --failed
```

### 4. Configuration Management

```bash
# Validate configuration
ga-red config validate config.yaml

# Display configuration (with YAML syntax highlighting)
ga-red config show config.yaml

# Convert YAML to JSON
ga-red config convert config.yaml --output config.json

# Generate template configuration
ga-red config template tap --output my_attack.yaml

# Available templates: tap, gcg, pair, basic
ga-red config template gcg
```

## Examples

### Complete Workflow

1. Generate a template configuration:
   ```bash
   ga-red config template tap --output my_tap_attack.yaml
   ```

2. Edit the configuration file with your settings

3. Validate the configuration:
   ```bash
   ga-red config validate my_tap_attack.yaml
   ```

4. Run the attack and monitor (with live progress):
   ```bash
   ga-red run my_tap_attack.yaml --monitor
   ```

5. Export results to CSV:
   ```bash
   ga-red results 123 --csv results.csv
   ```

### Quick Status Check

```bash
# List recent jobs (formatted table)
ga-red jobs list --limit 10

# Check specific job (colored panels)
ga-red jobs get 456 --results
```

## Visual Features

The CLI now includes:
- ✅ Color-coded status indicators (pending, running, completed, failed)
- 📊 Formatted tables for job listings
- 🎨 Syntax highlighting for YAML and JSON output
- 📈 Progress bars for monitoring operations
- 🔲 Styled panels for important information
- 🌈 Rich text formatting throughout

## Environment Variables

- `GA_KEY`: API key for authentication (required)
- `REDIT_API_URL`: REDit server URL (default: http://localhost:8000)

## Help

Get help for any command:
```bash
ga-red --help
ga-red jobs --help
ga-red run --help
ga-red results --help
ga-red config --help
```

## Requirements

- Python 3.7+
- Dependencies:
  - `pyyaml` - YAML configuration parsing
  - `requests` - HTTP client for API calls
  - `python-dotenv` - Environment variable management
  - `rich` - Terminal formatting and styling
