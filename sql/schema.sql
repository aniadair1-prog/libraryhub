-- LibraryHub database schema
-- Run this inside an empty libraryhub database.

CREATE TABLE books (
    book_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    published_year INTEGER
);

CREATE TABLE authors (
    author_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE book_authors (
    book_id INTEGER NOT NULL REFERENCES books(book_id)
        ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES authors(author_id)
        ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

CREATE TABLE members (
    member_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    joined_on DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE loans (
    loan_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(book_id),
    member_id INTEGER NOT NULL REFERENCES members(member_id),
    borrowed_on DATE NOT NULL DEFAULT CURRENT_DATE,
    due_on DATE NOT NULL,
    returned_on DATE,
    CHECK (due_on >= borrowed_on),
    CHECK (
        returned_on IS NULL
        OR returned_on >= borrowed_on
    )
);

CREATE UNIQUE INDEX one_active_loan_per_book
    ON loans(book_id)
    WHERE returned_on IS NULL;

CREATE INDEX idx_loans_due_on
    ON loans(due_on);