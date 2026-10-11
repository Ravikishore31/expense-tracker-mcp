import os
import sqlite3
from pathlib import Path
from fastmcp import FastMCP

# --------------------------------------------------
# Configuration
# --------------------------------------------------

mcp = FastMCP(name="expense_tracker")

# Store the database in a dedicated directory
# inside the current user's home directory.
DATA_DIR = Path.home() / ".expense_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

db_path = DATA_DIR / "expenses.db"


# --------------------------------------------------
# Database connection
# --------------------------------------------------

def get_db_connection():
    """Create a connection to the SQLite database."""
    return sqlite3.connect(str(db_path), timeout=10)


# --------------------------------------------------
# Initialize database
# --------------------------------------------------

def init_db():
    """Create the expenses table if it does not exist."""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL CHECK (amount >= 0),
                    date TEXT NOT NULL
                )
            """)

        print(f"Database initialized at: {db_path}")

    except sqlite3.Error as e:
        print(f"Database initialization failed: {e}")
        raise


# Initialize before starting the MCP server
init_db()


# --------------------------------------------------
# Tool 1: Add an expense
# --------------------------------------------------

@mcp.tool
def add_expense(description: str, amount: float, date: str):
    """Add a new expense to the database.

    Args:
        description: Description of the expense.
        amount: Expense amount; must be non-negative.
        date: Expense date in YYYY-MM-DD format.
    """
    if not description.strip():
        return {
            "status": "error",
            "message": "Description cannot be empty."
        }

    if amount < 0:
        return {
            "status": "error",
            "message": "Amount cannot be negative."
        }

    try:
        # Validate the date format
        from datetime import date as Date
        Date.fromisoformat(date)

        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO expenses (description, amount, date)
                VALUES (?, ?, ?)
                """,
                (description.strip(), amount, date),
            )

            expense_id = cursor.lastrowid

        return {
            "status": "success",
            "message": "Expense added successfully.",
            "expense_id": expense_id,
            "description": description.strip(),
            "amount": amount,
            "date": date,
        }

    except ValueError:
        return {
            "status": "error",
            "message": "Invalid date. Use YYYY-MM-DD format."
        }

    except sqlite3.Error as e:
        return {
            "status": "error",
            "message": f"Failed to save expense: {e}"
        }


# --------------------------------------------------
# Tool 2: List all expenses
# --------------------------------------------------

@mcp.tool
def list_expenses():
    """List all expenses in the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, description, amount, date
                FROM expenses
                ORDER BY date DESC, id DESC
                """
            )

            rows = cursor.fetchall()

        expenses = [
            {
                "id": row[0],
                "description": row[1],
                "amount": row[2],
                "date": row[3],
            }
            for row in rows
        ]

        return {
            "status": "success",
            "count": len(expenses),
            "expenses": expenses,
        }

    except sqlite3.Error as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve expenses: {e}"
        }


# --------------------------------------------------
# Tool 3: List expenses between dates
# --------------------------------------------------

@mcp.tool
def list_expenses_between_dates(
    start_date: str,
    end_date: str
):
    """List expenses between two dates, inclusive.

    Args:
        start_date: Starting date in YYYY-MM-DD format.
        end_date: Ending date in YYYY-MM-DD format.
    """
    from datetime import date as Date

    try:
        start = Date.fromisoformat(start_date)
        end = Date.fromisoformat(end_date)

        if start > end:
            return {
                "status": "error",
                "message": "Start date must be before or equal to end date."
            }

        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, description, amount, date
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (start_date, end_date),
            )

            rows = cursor.fetchall()

        expenses = [
            {
                "id": row[0],
                "description": row[1],
                "amount": row[2],
                "date": row[3],
            }
            for row in rows
        ]

        return {
            "status": "success",
            "count": len(expenses),
            "start_date": start_date,
            "end_date": end_date,
            "expenses": expenses,
        }

    except ValueError:
        return {
            "status": "error",
            "message": "Invalid date. Use YYYY-MM-DD format."
        }

    except sqlite3.Error as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve expenses: {e}"
        }


# --------------------------------------------------
# Run MCP server
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
    )