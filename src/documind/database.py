import psycopg
from pgvector.psycopg import register_vector
from documind.config import settings

def get_connection()->psycopg.connection:
    conn = psycopg.connect(settings.database_url)
    register_vector(conn)
    return conn

def init_db()->None:
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
    print("pgvector extension enabled.")
