"""
MAHI AI Database Migration & Schema Sync Script
Applies all SQLAlchemy declarative schemas and seeds initial administrative structures.
"""
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import get_settings
from backend.app.core.logging import logger
from backend.app.db.session import engine, init_db, SessionLocal
from backend.app.db import models

settings = get_settings()


def run_migrations():
    logger.info(f"Applying database migrations to: {settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url}")
    try:
        init_db()
        db = SessionLocal()
        user_count = db.query(models.User).count()
        dept_count = db.query(models.Department).count()
        db.close()
        logger.info(f"Migration completed successfully! Found {user_count} user(s) and {dept_count} department(s).")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
