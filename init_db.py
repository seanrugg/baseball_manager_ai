#!/usr/bin/env python3
"""
Database initialization script for Baseball Manager AI.

This script:
1. Creates database tables
2. Initializes indexes
3. Creates sample data (optional)
4. Validates database connection
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging

from dotenv import load_dotenv
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def check_database_connection():
    """Check if database is accessible."""
    logger.info("Checking database connection...")

    try:
        from baseball_manager_ai.database import get_db_connection

        connection = get_db_connection()
        if connection.test_connection():
            logger.info("✓ Database connection successful")
            return True
        else:
            logger.error("✗ Database connection failed")
            return False
    except Exception as e:
        logger.error(f"✗ Database connection error: {e}")
        return False


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")

    try:
        from baseball_manager_ai.database import init_db

        init_db()
        logger.info("✓ Database tables created")
        return True
    except Exception as e:
        logger.error(f"✗ Error creating tables: {e}")
        return False


def create_indexes():
    """Create database indexes."""
    logger.info("Creating database indexes...")

    try:
        from baseball_manager_ai.database import get_db_connection

        connection = get_db_connection()
        session = connection.get_session()

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_games_date ON games(date)",
            "CREATE INDEX IF NOT EXISTS idx_games_teams ON games(home_team, away_team)",
            "CREATE INDEX IF NOT EXISTS idx_players_team_pos ON players(team, position)",
            "CREATE INDEX IF NOT EXISTS idx_decisions_game ON manager_decisions(game_id)",
            "CREATE INDEX IF NOT EXISTS idx_decisions_inning ON manager_decisions(inning)",
            "CREATE INDEX IF NOT EXISTS idx_simulations_teams ON simulation_results(home_team, away_team)",
            "CREATE INDEX IF NOT EXISTS idx_team_stats_season ON team_stats(team, season)",
        ]

        for index_sql in indexes:
            try:
                session.execute(text(index_sql))
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")

        session.commit()
        logger.info("✓ Database indexes created")
        return True

    except Exception as e:
        logger.error(f"✗ Error creating indexes: {e}")
        return False


def validate_tables():
    """Validate that all tables exist."""
    logger.info("Validating database tables...")

    required_tables = [
        'games',
        'players',
        'play_by_play',
        'manager_decisions',
        'simulation_results',
        'team_stats'
    ]

    try:
        from baseball_manager_ai.database import get_db_connection

        connection = get_db_connection()
        session = connection.get_session()

        missing_tables = []
        for table_name in required_tables:
            result = session.execute(
                text(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='{table_name}')")
            )
            exists = result.scalar()

            if exists:
                logger.info(f"  ✓ Table '{table_name}' exists")
            else:
                logger.warning(f"  ✗ Table '{table_name}' missing")
                missing_tables.append(table_name)

        session.close()

        if missing_tables:
            logger.error(f"✗ Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            logger.info("✓ All required tables exist")
            return True

    except Exception as e:
        logger.error(f"✗ Error validating tables: {e}")
        return False


def get_database_stats():
    """Get database statistics."""
    logger.info("Database Statistics:")

    try:
        from baseball_manager_ai.database import get_db_connection

        connection = get_db_connection()
        session = connection.get_session()

        stats_query = """
        SELECT
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            (SELECT count(*) FROM {} ) as rows
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """

        result = session.execute(text("""
            SELECT
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """))

        for row in result:
            logger.info(f"  {row[0]:30s} {row[1]:>10s}")

        session.close()

    except Exception as e:
        logger.warning(f"Could not retrieve database stats: {e}")


def main():
    """Run database initialization."""
    logger.info("=" * 60)
    logger.info("BASEBALL MANAGER AI - DATABASE INITIALIZATION")
    logger.info("=" * 60)
    logger.info("")

    steps = [
        ("Check Connection", check_database_connection),
        ("Create Tables", create_tables),
        ("Create Indexes", create_indexes),
        ("Validate Tables", validate_tables),
    ]

    results = {}
    for step_name, step_func in steps:
        try:
            results[step_name] = step_func()
        except Exception as e:
            logger.error(f"Unexpected error in {step_name}: {e}")
            results[step_name] = False

        logger.info("")

    # Database stats
    try:
        get_database_stats()
    except Exception as e:
        logger.warning(f"Could not get database stats: {e}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("INITIALIZATION STATUS")
    logger.info("=" * 60)

    for step_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{step_name:20s} {status}")

    logger.info("")

    all_passed = all(results.values())

    if all_passed:
        logger.info("✓ Database initialization complete!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Start the API server")
        logger.info("     python -m baseball_manager_ai.api.model_server")
        logger.info("")
        logger.info("  2. Test the health endpoint")
        logger.info("     curl http://localhost:8000/health")
        logger.info("")
        logger.info("  3. Download data and train models (optional)")
        logger.info("     python scripts/download_data.py")
        logger.info("     python scripts/train_model.py --model all")
        return 0
    else:
        logger.error("✗ Database initialization failed")
        logger.error("")
        logger.error("Troubleshooting tips:")
        logger.error("  • Check DATABASE_URL in .env")
        logger.error("  • Verify PostgreSQL is running")
        logger.error("  • Check database credentials")
        logger.error("  • Review logs for detailed errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
