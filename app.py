"""Expense tracker: FastAPI backend + SQLite + vanilla JS frontend.

API:
    GET    /api/expenses?category=&month=YYYY-MM   list (newest first)
    POST   /api/expenses                          add one
    DELETE /api/expenses/{id}                     delete one
    GET    /api/summary?month=YYYY-MM             totals for a month
    GET    /                                      the web UI (static files)
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

CATEGORIES = ["Food", "Transport", "Housing", "Entertainment", "Health", "Shopping", "Other"]
DB_PATH = os.environ.get("EXPENSE_DB", "expenses.db")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
_write_lock = threading.Lock()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                amount     REAL NOT NULL,
                category   TEXT NOT NULL,
                date       TEXT NOT NULL,
                note       TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()


class ExpenseCreate(BaseModel):
    amount: float = Field(gt=0, description="Amount in dollars, must be positive")
    category: str
    date: date
    note: str = ""

    def validate_category(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(CATEGORIES)}")


class ExpenseOut(BaseModel):
    id: int
    amount: float
    category: str
    date: str
    note: str


def row_to_expense(row: sqlite3.Row) -> ExpenseOut:
    return ExpenseOut(
        id=row["id"],
        amount=row["amount"],
        category=row["category"],
        date=row["date"],
        note=row["note"],
    )


app = FastAPI(title="Expense Tracker")
init_db()


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/categories")
def list_categories():
    return {"categories": CATEGORIES}


@app.get("/api/expenses", response_model=list[ExpenseOut])
def list_expenses(
    category: str | None = Query(default=None),
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
):
    """List expenses, newest first. Filter by category and/or month (YYYY-MM)."""
    query = "SELECT * FROM expenses"
    clauses, params = [], []
    if category:
        clauses.append("category = ?")
        params.append(category)
    if month:
        clauses.append("substr(date, 1, 7) = ?")
        params.append(month)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY date DESC, id DESC"
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [row_to_expense(r) for r in rows]


@app.post("/api/expenses", response_model=ExpenseOut, status_code=201)
def add_expense(payload: ExpenseCreate):
    """Add one expense."""
    if payload.category not in CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"category must be one of: {', '.join(CATEGORIES)}",
        )
    with _write_lock:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO expenses (amount, category, date, note) VALUES (?, ?, ?, ?)",
                (payload.amount, payload.category, payload.date.isoformat(), payload.note),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM expenses WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return row_to_expense(row)


@app.delete("/api/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int):
    """Delete one expense by id."""
    with _write_lock:
        with get_db() as conn:
            cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="expense not found")


@app.get("/api/summary")
def monthly_summary(month: str = Query(pattern=r"^\d{4}-\d{2}$")):
    """Monthly totals for a month (YYYY-MM): grand total, count, per-category totals."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) AS n, SUM(amount) AS total "
            "FROM expenses WHERE substr(date, 1, 7) = ? GROUP BY category ORDER BY total DESC",
            (month,),
        ).fetchall()
        grand = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0) AS total "
            "FROM expenses WHERE substr(date, 1, 7) = ?",
            (month,),
        ).fetchone()
    by_category = {r["category"]: round(r["total"], 2) for r in rows}
    return {
        "month": month,
        "total": round(grand["total"], 2),
        "count": grand["n"],
        "by_category": by_category,
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    init_db()
    uvicorn.run(app, host="127.0.0.1", port=8000)
