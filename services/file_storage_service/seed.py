"""Начальные данные File Storage Service."""
import sqlite3


def seed_file_storage_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM attachments").fetchone()[0] > 0:
        return
    conn.executemany(
        """
        INSERT INTO attachments (id, entity_type, entity_id, file_name, file_url, file_size, uploaded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("att-001", "RESEARCH", "res-001", "interview_guide.pdf", "s3://pdp-files/interview_guide.pdf", 245760, "user-002"),
            ("att-002", "HYPOTHESIS", "hyp-001", "credit_form_prototype.png", "s3://pdp-files/credit_form_prototype.png", 512000, "user-001"),
        ],
    )
    conn.commit()
