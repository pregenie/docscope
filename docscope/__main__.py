#!/usr/bin/env python3
"""
DocScope main entry point - allows running with python -m docscope
This automatically starts the UI for easy setup.
"""

import sys
from .cli.cli import cli

if __name__ == "__main__":
    # If no arguments provided, default to 'start' command
    if len(sys.argv) == 1:
        sys.argv.append('start')
    
    cli()