# app/core/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings
from app.core.logging import logger

# The standard calling form is to send the URL <database_urls> as the first positional argument, usually a string that indicates database dialect and connection arguments:

#     engine = create_engine("postgresql+psycopg2://scott:tiger@localhost/test")
logger.info("Creating database engine with URL: %s", settings.DATABASE_URL)
engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    logger.debug("New database session created: %s", db)
    try:
        logger.debug("Using database session: %s", db)
        yield db
    except Exception as e:
        logger.exception("Database session error: %s", e)
        raise
    finally:
        logger.debug("Closing database session: %s", db)
        db.close()