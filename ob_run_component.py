#!/usr/bin/env python3
"""
Omnibenchmark dispatcher for spatially_variable_genes repository.

This script routes execution to the appropriate component (data_loader, methods, metrics)
based on the --component parameter, and forwards all other arguments to that component.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def find_component_script(component_path):
    """
    Find the script file for a given component.

    Args:
        component_path: Path to component (e.g., "data_loader", "methods/boostgp")

    Returns:
        Path to the script file (.py or .R)
    """
    repo_root = Path(__file__).parent.resolve()
    component_dir = repo_root / component_path

    if not component_dir.exists():
        raise FileNotFoundError(f"Component directory not found: {component_dir}")

    # Look for Python script
    python_script = component_dir / "script.py"
    if python_script.exists():
        return python_script, "python"

    # Look for R script
    r_script = component_dir / "script.R"
    if r_script.exists():
        return r_script, "R"

    # For data_loader, check for load_spatial_data.py
    if component_path == "data_loader":
        loader_script = component_dir / "load_spatial_data.py"
        if loader_script.exists():
            return loader_script, "python"

    raise FileNotFoundError(f"No script.py or script.R found in {component_dir}")

def main():
    # First pass: extract --component argument
    parser = argparse.ArgumentParser(
        description='Omnibenchmark dispatcher for spatially_variable_genes',
        add_help=False  # We'll parse remaining args later
    )
    parser.add_argument('--component', type=str, required=True,
                       help='Component to run (e.g., data_loader, methods/boostgp)')

    # Parse known args to get --component
    args, remaining_args = parser.parse_known_args()

    component_path = args.component

    print(f"[Dispatcher] Routing to component: {component_path}", flush=True)
    print(f"[Dispatcher] Forwarding arguments: {' '.join(remaining_args)}", flush=True)

    try:
        script_path, script_type = find_component_script(component_path)
        print(f"[Dispatcher] Found {script_type} script: {script_path}", flush=True)

        # Filter arguments based on component type
        filtered_args = []
        skip_next = False

        for arg in remaining_args:
            if skip_next:
                skip_next = False
                continue

            # Remove --data.solution for methods (except true_ranking) and data_loader
            if arg == '--data.solution':
                if 'true_ranking' not in component_path and 'metrics' not in component_path:
                    skip_next = True
                    print(f"[Dispatcher] Removing --data.solution (not needed by this component)", flush=True)
                    continue

            # Remove --name for metric collectors
            if arg == '--name':
                if 'metric_collector' in component_path:
                    skip_next = True
                    print(f"[Dispatcher] Removing --name (not needed by metric collector)", flush=True)
                    continue

            filtered_args.append(arg)

        remaining_args = filtered_args

        # Build command based on script type
        if script_type == "python":
            cmd = [sys.executable, str(script_path)] + remaining_args
        else:  # R
            cmd = ["Rscript", str(script_path)] + remaining_args

        print(f"[Dispatcher] Executing: {' '.join(cmd)}", flush=True)

        # Execute the component script
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)

    except FileNotFoundError as e:
        print(f"[Dispatcher] ERROR: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[Dispatcher] ERROR: Component script failed with exit code {e.returncode}",
              file=sys.stderr, flush=True)
        sys.exit(e.returncode)
    except Exception as e:
        print(f"[Dispatcher] ERROR: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
