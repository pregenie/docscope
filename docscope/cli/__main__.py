#!/usr/bin/env python3
"""
DocScope CLI entry point - allows running with python -m docscope.cli
"""

from .cli import cli

if __name__ == "__main__":
    cli()