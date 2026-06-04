from pathlib import Path
from documind.database import get_connection

MIGRATIONS_DIRECTORY_PATH = Path(__file__).parent.parent.parent / "migrations"

def run_migrations()->None:
    print(MIGRATIONS_DIRECTORY_PATH)
    files = sorted(MIGRATIONS_DIRECTORY_PATH.glob("*.sql"))
    with get_connection() as conn:
        for file in files:
            print(f"Applying {file.name} ...")
            with conn.cursor() as cur:
                cur.execute(file.read_text())
        conn.commit()
    print(f"Applied {len(files)} migration(s).")

if __name__ == "__main__":
    run_migrations()