#!/usr/bin/env -S uv run
# Run omnibenchmark on the host.
# /// script
# requires-python = "==3.12"
# dependencies = [
#     "omnibenchmark==0.3.2",
# ]
# ///
"""
Simple UV script to run omnibenchmark 0.3.2
Usage: ./run-omnibenchmark.py benchmark.yaml
"""

import sys
import subprocess

def main():
    # Call omnibenchmark CLI
    cmd = ["ob", "run", "benchmark", "-b", "benchmark.yaml"]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
