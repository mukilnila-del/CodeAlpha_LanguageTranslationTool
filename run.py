import os
import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    port = Config.PORT
    debug = Config.DEBUG
    print(f"[*] Starting Language Translation Server on http://127.0.0.1:{port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
