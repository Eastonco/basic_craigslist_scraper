"""
Shim to preserve the previous uvicorn target `server:app`.
The real FastAPI app now lives in the src package.
You can still run:
  uvicorn server:app --reload
But prefer:
  uvicorn basic_craigslist_scraper.server:app --reload
"""

import os
import sys

_src = os.path.join(os.path.dirname(__file__), "src")
if os.path.isdir(_src) and _src not in sys.path:
    sys.path.insert(0, _src)

from basic_craigslist_scraper.server import app  # noqa: F401
