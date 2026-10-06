import sys
import os
sys.path.insert(0, os.path.abspath("."))

try:
    from backend.app.main import app
    print("FastAPI app imported successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
