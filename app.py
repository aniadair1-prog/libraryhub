from datetime import date
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv(
    "SECRET_KEY",
    "development-only-key",
)

def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL was not loaded from .env")

    return psycopg.connect(database_url)


@app.route("/")
def home():
    search_term = request.args.get("search", "").strip()
    search_pattern = f"%{search_term}%"

    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    b.book_id,
                    b.title,
                    b.isbn,
                    b.published_year,
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM loans AS l
                            WHERE l.book_id = b.book_id
                              AND l.returned_on IS NULL
                        )
                        THEN 'on loan'
                        ELSE 'available'
                    END AS availability,
                    COALESCE(
                        STRING_AGG(
                            a.name,
                            ', '
                            ORDER BY a.name
                        ),
                        ''
                    ) AS authors
                FROM books AS b
                LEFT JOIN book_authors AS ba
                    ON ba.book_id = b.book_id
                LEFT JOIN authors AS a
                    ON a.author_id = ba.author_id
                WHERE (
                    %s = ''
                    OR b.title ILIKE %s
                    OR a.name ILIKE %s
                )
                GROUP BY
                    b.book_id,
                    b.title,
                    b.isbn,
                    b.published_year
                ORDER BY b.title
                """,
                (
                    search_term,
                    search_pattern,
                    search_pattern,
                ),
            )
            books = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    (
                        SELECT COUNT(*)
                        FROM books
                    ) AS total_books,

                    (
                        SELECT COUNT(*)
                        FROM books AS b
                        WHERE NOT EXISTS (
                            SELECT 1
                            FROM loans AS l
                            WHERE l.book_id = b.book_id
                              AND l.returned_on IS NULL
                        )
                    ) AS available_books,

                    (
                        SELECT COUNT(*)
                        FROM loans
                        WHERE returned_on IS NULL
                    ) AS active_loans,

                    (
                        SELECT COUNT(*)
                        FROM loans
                        WHERE returned_on IS NULL
                          AND due_on < CURRENT_DATE
                    ) AS overdue_loans
                """
            )
            stats = cursor.fetchone()

    return render_template(
        "index.html",
        books=books,
        search_term=search_term,
        stats=stats,
    )
@app.route("/loans")
def loans():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                SELECT
                    l.loan_id,
                    b.title,
                    m.name AS member,
                    l.borrowed_on,
                    l.due_on,
                    l.returned_on,
                    CASE
                        WHEN l.returned_on IS NOT NULL
                            THEN 'returned'
                        WHEN l.due_on < CURRENT_DATE
                            THEN 'overdue'
                        ELSE 'on loan'
                    END AS status
                FROM loans AS l
                JOIN books AS b
                    ON b.book_id = l.book_id
                JOIN members AS m
                    ON m.member_id = l.member_id
                ORDER BY
                    CASE
                        WHEN l.returned_on IS NULL THEN 0
                        ELSE 1
                    END,
                    l.due_on
            """)
            loan_records = cursor.fetchall()

    return render_template(
        "loans.html",
        loan_records=loan_records,
    )
@app.post("/loans/<int:loan_id>/return")
def return_book(loan_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE loans
                SET returned_on = CURRENT_DATE
                WHERE loan_id = %s
                  AND returned_on IS NULL
                """,
                (loan_id,),
            )
            connection.commit()

    return redirect(url_for("loans"))
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            if request.method == "POST":
                book_id = request.form["book_id"]
                member_id = request.form["member_id"]
                due_on = request.form["due_on"]

                if due_on < date.today().isoformat():
                    flash(
                        "The due date cannot be in the past.",
                        "error",
                    )
                    return redirect(url_for("checkout"))

                cursor.execute(
                    """
                    INSERT INTO loans
                        (book_id, member_id, due_on)
                    VALUES (%s, %s, %s)
                    """,
                    (book_id, member_id, due_on),
                )

                connection.commit()
                return redirect(url_for("loans"))

            cursor.execute("""
                SELECT
                    b.book_id,
                    b.title
                FROM books AS b
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM loans AS l
                    WHERE l.book_id = b.book_id
                      AND l.returned_on IS NULL
                )
                ORDER BY b.title
            """)
            books = cursor.fetchall()

            cursor.execute("""
                SELECT
                    member_id,
                    name
                FROM members
                ORDER BY name
            """)
            members = cursor.fetchall()

    return render_template(
        "checkout.html",
        books=books,
        members=members,
        today=date.today().isoformat(),
    )
@app.route("/members", methods=["GET", "POST"])
def members():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            if request.method == "POST":
                name = request.form["name"].strip()
                email = request.form["email"].strip()

                cursor.execute(
                    """
                    INSERT INTO members (name, email)
                    VALUES (%s, %s)
                    ON CONFLICT (email) DO NOTHING
                    """,
                    (name, email),
                )

                if cursor.rowcount == 0:
                    flash(
                        "That email is already registered.",
                        "error",
                    )
                else:
                    flash(
                        "Member added successfully.",
                        "success",
                    )

                connection.commit()
                return redirect(url_for("members"))

            cursor.execute("""
                SELECT
                    member_id,
                    name,
                    email,
                    joined_on
                FROM members
                ORDER BY name
            """)
            member_records = cursor.fetchall()

    return render_template(
        "members.html",
        member_records=member_records,
    )
@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"].strip()
        isbn = request.form["isbn"].strip() or None
        published_year = request.form["published_year"] or None

        author_names = [
            name.strip()
            for name in request.form["author_names"].split(",")
            if name.strip()
        ]

        if not author_names:
            flash(
                "Enter at least one author.",
                "error",
            )
            return redirect(url_for("add_book"))

        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO books
                        (title, isbn, published_year)
                    VALUES (%s, %s, %s)
                    RETURNING book_id
                    """,
                    (title, isbn, published_year),
                )
                book = cursor.fetchone()

                for author_name in author_names:
                    cursor.execute(
                        """
                        INSERT INTO authors (name)
                        VALUES (%s)
                        ON CONFLICT (name)
                        DO UPDATE SET name = EXCLUDED.name
                        RETURNING author_id
                        """,
                        (author_name,),
                    )
                    author = cursor.fetchone()

                    cursor.execute(
                        """
                        INSERT INTO book_authors
                            (book_id, author_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            book["book_id"],
                            author["author_id"],
                        ),
                    )

                connection.commit()

        flash("Book added successfully.", "success")
        return redirect(url_for("home"))

    return render_template("add_book.html")
if __name__ == "__main__":
    app.run(debug=True)