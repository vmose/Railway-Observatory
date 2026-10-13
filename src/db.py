import psycopg2
from src.config import database_url


def connect():
    """Use as `with connect() as conn:` -> commits on success, rolls back on error."""
    return psycopg2.connect(database_url())
