#!/usr/bin/env python3
"""KIND cluster deployment with FluxCD."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))  # app/

logging.basicConfig(
    format="[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO
)

from cli.cli import main

if __name__ == "__main__":
    main()
