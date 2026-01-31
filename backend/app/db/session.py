from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

DATABASE_URL = f"postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@localhost:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)