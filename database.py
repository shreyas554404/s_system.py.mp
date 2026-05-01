import sqlite3

def connect():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id TEXT PRIMARY KEY,
        password TEXT,
        name TEXT,
        role TEXT,
        salary REAL,
        days REAL,
        leaves REAL,
        tax REAL,
        pf_amount REAL,
        pf_no TEXT
    )
    """)

    conn.commit()
    conn.close()