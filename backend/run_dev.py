#!/usr/bin/env python3
"""
Development runner for Scorpio Backend
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main development runner"""

    # Add current directory to Python path
    sys.path.insert(0, str(Path(__file__).parent))

    # Set development environment
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")

    # Import and run the application
    try:
        import uvicorn
        from app.main import app

        print("🚀 Starting Scorpio Backend in development mode...")
        print("📍 API Documentation: http://localhost:8000/api/docs")
        print("🔍 Health Check: http://localhost:8000/health")

        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="debug"
        )

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("🔄 Please run this script again")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 Shutting down Scorpio Backend")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
