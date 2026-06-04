from documind.database import get_connection, init_db

init_db()

with get_connection() as conn:
    with conn.cursor() as cur:
        # Prove vector math works end-to-end
        cur.execute("SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector AS distance;")
        distance = cur.fetchone()[0]
        print(f"Cosine distance between [1,2,3] and [1,2,4]: {distance:.4f}")