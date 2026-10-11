import os
from fastmcp import FastMCP
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), "expenses.db")

mcp = FastMCP(
    name="expense_tracker"
)

def init_db():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

@mcp.tool
def add_expense(description: str, amount: float, date: str):
    """Add a new expense to the database."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (description, amount, date)
            VALUES (?, ?, ?)
        ''', (description, amount, date))
        conn.commit()
    return {"status": "success", "message": "Expense added successfully."}

@mcp.tool
def list_expenses():
    """List all expenses in the database."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM expenses')
        expenses = cursor.fetchall()
    return {"status": "success", "expenses": expenses}

@mcp.tool
def list_expenses_between_dates(start_date: str, end_date: str):
    """List expenses between two dates."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM expenses
            WHERE date BETWEEN ? AND ?
        ''', (start_date, end_date))
        expenses = cursor.fetchall()
    return {"status": "success", "expenses": expenses}


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )