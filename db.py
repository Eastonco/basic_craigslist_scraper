"""Single source of the Postgres engine, built from environment/.env."""
import os

from dotenv import load_dotenv

from models import get_engine

load_dotenv()


def get_engine_from_env(echo: bool = False):
    return get_engine(
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "craigslist"),
        echo=echo,
    )
