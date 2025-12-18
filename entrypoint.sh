#!/bin/bash
# Simple entrypoint that uses uv to install dependencies and executes the module script

#set -euo pipefail

# Install module dependencies using uv with the legacy Python version
# Try mounted requirements first, fall back to baked-in version
INSTALL_DIR="$(pwd)/local_python_libs"
mkdir -p "$INSTALL_DIR"
echo "UV INSTALL..."
uv pip install --python python-legacy -r /mnt/requirements-module.txt --target $INSTALL_DIR --no-system

# Change to home directory where omnibenchmark expects output structure
# cd $HOME

export PYTHONPATH="$INSTALL_DIR:$PYTHONPATH"

# Execute the module script with the legacy Python version
# Script is expected to be mounted in /mnt (current working directory from docker run)
exec python-legacy ob_run_component.py "$@"
