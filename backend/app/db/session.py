from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.url import get_postgres_url


engine = create_engine(get_postgres_url("psycopg2"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)