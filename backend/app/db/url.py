from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy.engine import make_url


# Get backend directory: app/db/url.py -> go up 3 levels to backend/
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


def load_backend_env() -> None:
    for env_file in (BACKEND_ROOT / ".env.db", BACKEND_ROOT / ".env"):
        if env_file.exists():
            load_dotenv(env_file, override=True)


def get_postgres_url(driver: str = "psycopg2") -> str:
    load_backend_env()

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        url_obj = make_url(database_url).set(drivername=f"postgresql+{driver}")
        host_override = os.getenv("DATABASE_HOST_OVERRIDE")
        if host_override:
            url_obj = url_obj.set(host=host_override)
        # Force IPv4 for local development to avoid IPv6 resolution differences.
        elif url_obj.host == "localhost":
            url_obj = url_obj.set(host="127.0.0.1")
        return url_obj.render_as_string(hide_password=False)

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")  # Use 127.0.0.1 instead of localhost
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB")

    if not all([user, password, database]):
        raise RuntimeError(
            "Missing PostgreSQL configuration. Set DATABASE_URL or POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB."
        )

    return f"postgresql+{driver}://{user}:{password}@{host}:{port}/{database}"
