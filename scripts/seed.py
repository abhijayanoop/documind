from documind.database import get_connection

DOCUMENTS = [
    # (tenant_id, document_id, title, content, access_level)
    ("cred", "doc_001", "CRED Interview Qs", "Explain consensus algorithms.", "public"),
    ("cred", "doc_002", "CRED Salary Bands", "ML engineers: 25-35 LPA.", "salary_tier"),
    ("cred", "doc_003", "CRED 2026 Hiring Plan", "Hire 100 ML engineers.", "hiring_manager"),
    ("razorpay", "doc_001", "Razorpay Interview Qs", "Design a payment gateway.", "public"),
    ("razorpay", "doc_002", "Razorpay Salary Bands", "ML engineers: 28-42 LPA.", "salary_tier"),
]

USERS = [
    # (tenant_id, user_id, role)
    ("cred", "candidate_1", "candidate"),
    ("cred", "manager_1", "hiring_manager"),
    ("razorpay", "candidate_2", "candidate"),
]


def seed() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO documents "
                "(tenant_id, document_id, title, content, access_level) "
                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (tenant_id, document_id) DO NOTHING",
                DOCUMENTS,
            )
            cur.executemany(
                "INSERT INTO user_roles (tenant_id, user_id, role) "
                "VALUES (%s,%s,%s) ON CONFLICT (tenant_id, user_id) DO NOTHING",
                USERS,
            )
        conn.commit()
    print(f"Seeded {len(DOCUMENTS)} docs, {len(USERS)} users.")


if __name__ == "__main__":
    seed()