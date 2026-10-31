\# LibraryHub



LibraryHub is a library management application built with Flask and PostgreSQL.



It allows users to manage books, authors, members, and loans while demonstrating relational database design and common DBMS concepts.



\## Features



\- View books and authors

\- Add books with one or multiple authors

\- Register library members

\- Check books out to members

\- Return books

\- Detect overdue loans

\- Display book availability

\- Search by title or author

\- Show dashboard statistics

\- Prevent duplicate member emails

\- Prevent multiple active loans for the same book

\- Validate loan dates

\- Display database integrity test results



\## Technologies



\- Python

\- Flask

\- PostgreSQL

\- Psycopg

\- Jinja2

\- HTML

\- CSS



\## Database design



The application contains five main tables:



```text

books

authors

book\_authors

members

loans



Setup

1\. Create the database

Create a PostgreSQL database named:



libraryhub

2\. Create the tables

Run the SQL in:



sql/schema.sql

3\. Create the environment file

Create a file named .env in the project folder:



DATABASE\_URL=postgresql://postgres:YOUR\_PASSWORD@localhost:5432/libraryhub

Replace YOUR\_PASSWORD with your local PostgreSQL password.



Never commit .env to GitHub.



4\. Install dependencies

py -m pip install flask "psycopg\[binary]" python-dotenv

5\. Run the tests

py test\_libraryhub.py

Expected output:



All LibraryHub database tests passed.

6\. Start the application

py app.py

Open:



http://127.0.0.1:5000

DBMS concepts demonstrated

This project demonstrates:



Primary keys

Foreign keys

One-to-many relationships

Many-to-many relationships

Junction tables

Unique constraints

Check constraints

Partial unique indexes

Joins

Aggregation

GROUP BY

ILIKE searches

Parameterized SQL

Transactions

Derived availability status

Data-integrity testing

Future improvements

User authentication

Role-based permissions

Edit and delete books

Pagination

Export reports to CSV

Book cover images

Automated web tests

Database migrations

Docker deployment

Cloud deployment

Security notes

SQL values are passed using parameterized queries.



The PostgreSQL password is stored in .env, and .env is excluded through .gitignore.



This project is intended for local development and portfolio demonstration.



