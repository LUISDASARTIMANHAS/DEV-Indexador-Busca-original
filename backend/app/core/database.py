# app/core/database.py

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings
from app.core.logging import logger

# The standard calling form is to send the URL <database_urls> as the first positional argument, usually a string that indicates database dialect and connection arguments:

#     engine = create_engine("postgresql+psycopg2://scott:tiger@localhost/test")
database_url = settings.get_database_url()
logger.info(
    "Creating database engine with URL: %s",
    make_url(database_url).render_as_string(hide_password=True),
)
engine = create_engine(database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    logger.debug("New database session created: %s", db)
    try:
        logger.debug("Using database session: %s", db)
        yield db
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Database session error: %s", exc)
        raise
    finally:
        logger.debug("Closing database session: %s", db)
        db.close()
