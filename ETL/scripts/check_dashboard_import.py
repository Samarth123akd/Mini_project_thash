"""Import the dashboard app without running the server to verify import-time readiness."""
import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path so top-level packages (dashboard, etl)
# can be imported when this script is executed from the scripts/ folder.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.app import create_app

app = create_app()
print('Flask app created. Routes:')
for rule in sorted([r.rule for r in app.url_map.iter_rules()]):
    print(' ', rule)
