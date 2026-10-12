from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
<<<<<<< HEAD

from app.db.url import get_postgres_url


engine = create_engine(get_postgres_url("psycopg2"))
=======
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env.db")

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)
>>>>>>> origin/main
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)