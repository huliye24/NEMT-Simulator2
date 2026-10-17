"""Entry point for the NEMT App cloud API.

Examples:
    python backend/trade_main.py
    uvicorn trade_app.main:create_app --factory --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


if __name__ == "__main__":
    uvicorn.run(
        "trade_app.main:create_app",
        factory=True,
        host=os.environ.get("NEMT_API_HOST", "127.0.0.1"),
        port=int(os.environ.get("NEMT_API_PORT", "8000")),
        reload=os.environ.get("NEMT_API_RELOAD", "0") == "1",
    )
