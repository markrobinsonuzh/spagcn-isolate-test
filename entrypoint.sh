#!/bin/bash
# Simple entrypoint that uses uv to install dependencies and executes the module script

#set -euo pipefail

# Install module dependencies using uv with the legacy Python version
# Try mounted requirements first, fall back to baked-in version
if [ -f /mnt/requirements-module.txt ]; then
    uv pip install --python python-legacy --system -r /mnt/requirements-module.txt
elif [ -f /app/requirements-module.txt ]; then
    uv pip install --python python-legacy --system -r /app/requirements-module.txt
fi

# Change to home directory where omnibenchmark expects output structure
cd $HOME

# Execute the module script with the legacy Python version
# Script is expected to be mounted in /mnt (current working directory from docker run)
exec python-legacy /mnt/ob_run_component.py "$@"
