from documind.database import get_connection

DOCUMENTS = [
    # (tenant_id, document_id, title, content, access_level)

    # ---- CRED ----
    ("cred", "doc_001", "CRED Engineering Interview Guide",
     "CRED's technical interviews for engineering roles focus heavily on distributed "
     "systems fundamentals. Candidates should be prepared to explain consensus algorithms "
     "such as Raft and Paxos, how leader election works, and how systems achieve fault "
     "tolerance. The interview also covers data structures, system design, and questions "
     "on eventual consistency versus strong consistency in distributed databases.",
     "public"),

    ("cred", "doc_002", "CRED ML Engineer Compensation Bands",
     "Compensation for machine learning engineers at CRED is structured by level. "
     "Mid-level ML engineers earn a base salary in the range of 25 to 35 LPA, along with "
     "ESOPs and performance bonuses. Senior ML engineers earn between 40 and 60 LPA. "
     "These bands are reviewed annually and vary with experience and specialisation.",
     "salary_tier"),

    ("cred", "doc_003", "CRED 2026 Hiring Plan",
     "CRED plans to expand its machine learning and AI engineering teams significantly in "
     "2026, with a target of hiring 100 engineers across ML infrastructure, fraud detection, "
     "and recommendation systems. Hiring will prioritise candidates with production "
     "experience in RAG systems, agentic workflows, and model evaluation.",
     "hiring_manager"),

    ("cred", "doc_004", "CRED Internal Onboarding Notes",
     "New engineers at CRED complete a two-week onboarding covering the internal "
     "microservices architecture, the deployment pipeline, and on-call expectations. "
     "Engineers are assigned a buddy and ramp up on the codebase through starter tickets.",
     "internal"),

    # ---- Razorpay ----
    ("razorpay", "doc_001", "Razorpay Technical Interview Overview",
     "The Razorpay engineering interview covers the design of a payment gateway end to end, "
     "including idempotency of payment requests, handling webhooks, reconciliation, and "
     "ensuring exactly-once semantics in money movement. Candidates are also assessed on "
     "API design, database modelling for transactions, and handling failure and retries.",
     "public"),

    ("razorpay", "doc_002", "Razorpay ML Engineer Compensation Bands",
     "Machine learning engineers at Razorpay are compensated by level. Mid-level ML "
     "engineers earn a base salary between 28 and 42 LPA plus ESOPs. Senior engineers earn "
     "between 45 and 70 LPA. Compensation reflects experience, interview performance, and "
     "the specific team.",
     "salary_tier"),

    ("razorpay", "doc_003", "Razorpay Internal Engineering Practices",
     "Razorpay engineering teams follow trunk-based development with feature flags. "
     "All services require unit and integration test coverage before deploy, and "
     "payment-critical paths require an additional review from a senior engineer.",
     "internal"),
]

USERS = [
    # (tenant_id, user_id, role)
    ("cred", "candidate_1", "candidate"),
    ("cred", "manager_1", "hiring_manager"),
    ("cred", "admin_1", "admin"),
    ("razorpay", "candidate_2", "candidate"),
    ("razorpay", "manager_2", "hiring_manager"),
]


def seed() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO documents "
                "(tenant_id, document_id, title, content, access_level) "
                "VALUES (%s,%s,%s,%s,%s) "
                "ON CONFLICT (tenant_id, document_id) DO UPDATE SET "
                "title = EXCLUDED.title, content = EXCLUDED.content, "
                "access_level = EXCLUDED.access_level",
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