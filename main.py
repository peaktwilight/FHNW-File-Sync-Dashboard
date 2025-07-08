#!/usr/bin/env python3
"""
FHNW File Sync Dashboard - Main Entry Point

A modern, user-friendly file synchronization tool with profile management.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.main_window import main

if __name__ == "__main__":
    main()