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

def log_query(tenant_id: str, user_id: str, query_text: str, retrieved_doc_ids: list[str])->None:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO query_log 
                    (tenant_id, user_id, query_text, retrieved_doc_ids)
                    VALUES (%s, %s, %s, %s)
                """, (tenant_id, user_id, query_text, retrieved_doc_ids))
            conn.commit()
    except Exception as e:
        print(f"[audit] failed to log query: {e}")