#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""News Agent - Daily News Briefing Automation Tool"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.main import main

if __name__ == "__main__":
    main()
