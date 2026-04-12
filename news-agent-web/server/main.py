"""
News Agent Web - Backend Entry Point

This module re-exports from the structured app module.
For new development, use server/app/main.py directly.
"""

# Re-export the app from the structured module
from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
