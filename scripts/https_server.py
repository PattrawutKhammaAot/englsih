#!/usr/bin/env python3
"""HTTPS entry — run local_server with SSL."""
from local_server import main

if __name__ == "__main__":
    import sys

    if "--https" not in sys.argv:
        sys.argv.append("--https")
    main()
