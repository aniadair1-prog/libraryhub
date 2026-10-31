import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def main():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL was not loaded from .env")

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM books")
            total_books = cursor.fetchone()[0]
            assert total_books > 0, "Expected at least one book"

            cursor.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT email
                    FROM members
                    GROUP BY email
                    HAVING COUNT(*) > 1
                ) AS duplicate_emails
            """)
            duplicate_emails = cursor.fetchone()[0]
            assert duplicate_emails == 0, "Duplicate member emails found"

            cursor.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT book_id
                    FROM loans
                    WHERE returned_on IS NULL
                    GROUP BY book_id
                    HAVING COUNT(*) > 1
                ) AS duplicate_active_loans
            """)
            duplicate_active_loans = cursor.fetchone()[0]
            assert duplicate_active_loans == 0, (
                "A book has multiple active loans"
            )

            cursor.execute("""
                SELECT COUNT(*)
                FROM loans
                WHERE due_on < borrowed_on
                   OR (
                       returned_on IS NOT NULL
                       AND returned_on < borrowed_on
                   )
            """)
            invalid_dates = cursor.fetchone()[0]
            assert invalid_dates == 0, "Invalid loan dates found"

    print("All LibraryHub database tests passed.")


if __name__ == "__main__":
    main()