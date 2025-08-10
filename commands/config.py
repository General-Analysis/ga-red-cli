"""
Config command - Manage and validate configurations
"""

import argparse
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from utils import load_yaml_config, print_json

def add_parser(subparsers):
    """Add config command parser"""
    parser = subparsers.add_parser(
        'config',
        help='Manage and validate configurations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Configuration management utilities',
        epilog="""
Examples:
  ga-red config validate config.yaml     # Validate configuration
  ga-red config show config.yaml         # Display configuration
  ga-red config convert config.yaml      # Convert YAML to JSON
  ga-red config template tap             # Generate template config
        """
    )
    
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration file')
    validate_parser.add_argument('config_file', help='Configuration file to validate')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Display configuration')
    show_parser.add_argument('config_file', help='Configuration file to display')
    show_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert YAML to JSON')
    convert_parser.add_argument('config_file', help='Configuration file to convert')
    convert_parser.add_argument(
        '--output', '-o',
        help='Output file (default: print to stdout)'
    )
    
    # Template command
    template_parser = subparsers.add_parser('template', help='Generate template configuration')
    template_parser.add_argument(
        'attack_type',
        choices=['tap', 'gcg', 'pair', 'basic'],
        help='Type of attack configuration'
    )
    template_parser.add_argument(
        '--output', '-o',
        help='Output file (default: print to stdout)'
    )

def execute(args):
    """Execute config command"""
    if not args.action:
        print("Please specify an action: validate, show, convert, or template")
        print("Use 'ga-red config --help' for more information")
        return
    
    if args.action == 'validate':
        validate_config(args.config_file)
    elif args.action == 'show':
        show_config(args.config_file, args.json)
    elif args.action == 'convert':
        convert_config(args.config_file, args.output)
    elif args.action == 'template':
        generate_template(args.attack_type, args.output)

def validate_config(config_file: str):
    """Validate configuration file"""
    print(f"🔍 Validating configuration: {config_file}")
    
    # Load configuration
    config = load_yaml_config(config_file)
    if not config:
        print("❌ Failed to load configuration")
        return
    
    # Check required fields
    errors = []
    warnings = []
    
    # Check top-level structure
    if 'config' not in config:
        errors.append("Missing 'config' section")
    else:
        cfg = config['config']
        
        # Check attack configuration
        if 'attack' not in cfg:
            errors.append("Missing 'attack' configuration")
        elif 'type' not in cfg['attack']:
            errors.append("Missing attack type")
        
        # Check models configuration
        if 'models' not in cfg:
            warnings.append("Missing 'models' configuration")
        else:
            if 'target' not in cfg['models']:
                errors.append("Missing target model configuration")
            if 'attacker' not in cfg['models']:
                warnings.append("Missing attacker model configuration")
        
        # Check for objectives or dataset
        if 'objectives' not in cfg and 'dataset' not in cfg:
            errors.append("Must specify either 'objectives' or 'dataset'")
    
    # Display results
    if errors:
        print("\n❌ Validation failed with errors:")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not errors:
        print("✅ Configuration is valid")
        
        # Display configuration summary
        print("\n📋 Configuration Summary:")
        print(f"  Description: {config.get('description', 'N/A')}")
        
        if 'config' in config:
            cfg = config['config']
            if 'attack' in cfg:
                print(f"  Attack Type: {cfg['attack'].get('type', 'N/A')}")
            if 'models' in cfg:
                if 'target' in cfg['models']:
                    print(f"  Target Model: {cfg['models']['target'].get('name', 'N/A')}")
                if 'attacker' in cfg['models']:
                    print(f"  Attacker Model: {cfg['models']['attacker'].get('name', 'N/A')}")
            if 'dataset' in cfg:
                print(f"  Dataset: {cfg['dataset']}")
            elif 'objectives' in cfg:
                print(f"  Objectives: {len(cfg['objectives'])} defined")

def show_config(config_file: str, as_json: bool):
    """Display configuration file contents"""
    config = load_yaml_config(config_file)
    if not config:
        return
    
    if as_json:
        print_json(config)
    else:
        print(f"📄 Configuration: {Path(config_file).absolute()}\n")
        print(yaml.dump(config, default_flow_style=False, sort_keys=False))

def convert_config(config_file: str, output_file: Optional[str]):
    """Convert YAML configuration to JSON"""
    config = load_yaml_config(config_file)
    if not config:
        return
    
    json_str = json.dumps(config, indent=2)
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(json_str)
        
        print(f"✅ Configuration converted and saved to: {output_path.absolute()}")
    else:
        print(json_str)

def generate_template(attack_type: str, output_file: Optional[str]):
    """Generate template configuration"""
    templates = {
        'tap': {
            'description': 'TAP attack configuration template',
            'config': {
                'attack': {
                    'type': 'TAP',
                    'config': {
                        'branching_factor': 2,
                        'sub_branching_factor': 2,
                        'max_depth': 3,
                        'max_width': 5,
                        'score_threshold': 8.0
                    }
                },
                'target': {
                    'type': 'SimpleLLMTarget'
                },
                'scorer': {
                    'type': 'RubricBasedScorer'
                },
                'evaluator': {
                    'type': 'AdversarialEvaluator',
                    'use_agentic': False
                },
                'models': {
                    'target': {
                        'name': 'gpt-4o',
                        'temperature': 0
                    },
                    'attacker': {
                        'name': 'together_ai/deepseek-ai/DeepSeek-R1',
                        'temperature': 0
                    },
                    'evaluator': {
                        'name': 'together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo',
                        'temperature': 0
                    }
                },
                'dataset': 'your-dataset-name',
                'save_results': True,
                'output_path': 'results/tap_results.json'
            }
        },
        'gcg': {
            'description': 'GCG attack configuration template',
            'config': {
                'attack': {
                    'type': 'GCG',
                    'config': {
                        'num_steps': 500,
                        'batch_size': 512,
                        'topk': 256,
                        'search_width': 512
                    }
                },
                'target': {
                    'type': 'SimpleLLMTarget'
                },
                'models': {
                    'target': {
                        'name': 'gpt-3.5-turbo',
                        'temperature': 0
                    }
                },
                'objectives': [
                    'Your objective here'
                ],
                'save_results': True,
                'output_path': 'results/gcg_results.json'
            }
        },
        'pair': {
            'description': 'PAIR attack configuration template',
            'config': {
                'attack': {
                    'type': 'PAIR',
                    'config': {
                        'max_iterations': 20,
                        'max_conversation_length': 10
                    }
                },
                'target': {
                    'type': 'SimpleLLMTarget'
                },
                'models': {
                    'target': {
                        'name': 'gpt-4o',
                        'temperature': 0
                    },
                    'attacker': {
                        'name': 'gpt-4o',
                        'temperature': 0.7
                    }
                },
                'objectives': [
                    'Your objective here'
                ],
                'save_results': True,
                'output_path': 'results/pair_results.json'
            }
        },
        'basic': {
            'description': 'Basic attack configuration template',
            'config': {
                'attack': {
                    'type': 'SimpleAttack',
                    'config': {}
                },
                'target': {
                    'type': 'SimpleLLMTarget'
                },
                'models': {
                    'target': {
                        'name': 'gpt-3.5-turbo',
                        'temperature': 0
                    }
                },
                'objectives': [
                    'Your objective here'
                ],
                'save_results': True,
                'output_path': 'results/basic_results.json'
            }
        }
    }
    
    template = templates.get(attack_type)
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(template, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Template generated: {output_path.absolute()}")
        print(f"📝 Edit the file to customize your {attack_type.upper()} attack configuration")
    else:
        print(f"# {attack_type.upper()} Attack Configuration Template\n")
        print(yaml.dump(template, default_flow_style=False, sort_keys=False))
