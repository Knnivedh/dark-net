import os
import sys

# Set cloud mode flag
os.environ['CLOUD_MODE'] = 'true'

# Set cloud mode flag
os.environ['CLOUD_MODE'] = 'true'

from ui_bridge import app

if __name__ == "__main__":
    # Run with Gunicorn/Waitress in production, but for now standard run
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
