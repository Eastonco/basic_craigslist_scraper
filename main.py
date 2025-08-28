"""
Shim entrypoint for backward compatibility.
Delegates to the src package module so existing commands keep working:
  python main.py -c ./config/config.json
"""

import os
import sys

# Add src to sys.path for local runs outside Docker
_src = os.path.join(os.path.dirname(__file__), "src")
if os.path.isdir(_src) and _src not in sys.path:
    sys.path.insert(0, _src)

from basic_craigslist_scraper.app import main

if __name__ == "__main__":
    main()
