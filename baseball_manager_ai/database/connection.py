import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize()

    def _initialize(self):
        database_url = os.getenv(
            'DATABASE_URL',
            'mysql+pymysql://baseball_user:baseball_password@localhost:3306/baseball_db'
        )

        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=os.getenv('SQL_ECHO', 'false').lower() == 'true'
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info(f"Database connection initialized")

    def get_session(self) -> Session:
        return self.SessionLocal()

    def close(self):
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")

    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


_db_connection = None


def get_db_connection():
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def get_db() -> Session:
    connection = get_db_connection()
    return connection.get_session()


def init_db():
    from .models import Base
    connection = get_db_connection()
    Base.metadata.create_all(bind=connection.engine)
    logger.info("Database tables initialized")
