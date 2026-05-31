import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = os.getenv("DATABASE_URL", "postgresql://airflow:airflow@localhost:5432/market_intelligence")
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


def get_db_connection():
    engine = get_engine()
    return engine.connect()


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
