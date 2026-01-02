from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

Base = declarative_base()

def get_database_url():
    """Get database URL from environment or use default."""
    # Default to MySQL, but supports PostgreSQL too
    # MySQL format: mysql+mysqlconnector://user:password@host:port/database
    # PostgreSQL format: postgresql://user:password@host:port/database
    return os.getenv(
        'DATABASE_URL',
        'mysql+mysqlconnector://root:password@localhost:3306/forum_crawler'
    )

def create_db_engine():
    """Create database engine with connection pooling."""
    return create_engine(
        get_database_url(),
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        echo=False
    )

def get_session_maker():
    """Create session maker."""
    engine = create_db_engine()
    return sessionmaker(bind=engine)

def init_db():
    """Initialize database tables."""
    engine = create_db_engine()
    Base.metadata.create_all(engine)
