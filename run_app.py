import os
import sys
from pathlib import Path

# Ensure root directory is on python path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import uvicorn
from backend.config import API_HOST, API_PORT

if __name__ == "__main__":
    print("=" * 65)
    print("  EnterpriseFlow AI — Unified Multi-Agent Onboarding Platform")
    print("=" * 65)
    print(f"  • API & Web Dashboard: http://localhost:{API_PORT}")
    print(f"  • Interactive API Docs: http://localhost:{API_PORT}/docs")
    print("=" * 65)
    uvicorn.run("backend.main:app", host=API_HOST, port=API_PORT, reload=False)
