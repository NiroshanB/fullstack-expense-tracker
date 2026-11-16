# Expense Tracker — Full-Stack Web App

A full-stack expense tracker: a **FastAPI** backend with **SQLite**, and a **vanilla HTML/CSS/JavaScript** frontend (no frontend framework) served by the backend itself. Add expenses, filter them by category and month, delete them, and see monthly totals plus a per-category bar chart drawn with plain JavaScript canvas.

## Skills demonstrated

- Python, FastAPI, Pydantic validation
- SQL (SQLite) — filtering by category/month, GROUP BY totals
- REST API design
- HTML, CSS, JavaScript (vanilla, no framework) — fetch API, DOM updates, canvas chart
- Full-stack development: one codebase, backend serving both API and UI

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app:app --reload
```

Open `http://localhost:8000` in a browser. The API docs are at `http://localhost:8000/docs`.

## Features

- **Add an expense**: amount, category, date, note. Amount must be positive; category must be one of Food, Transport, Housing, Entertainment, Health, Shopping, Other.
- **List and filter**: filter expenses by category and by month.
- **Delete** an expense from the table.
- **Monthly totals**: grand total and expense count for the selected month, plus per-category totals — computed by the backend (`/api/summary`), shown in the UI.
- **Bar chart**: per-category totals for the month, drawn with plain JavaScript `<canvas>` (no chart library).

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/expenses?category=&month=YYYY-MM` | List expenses, newest first |
| `POST` | `/api/expenses` | Add one. Body: `{"amount": 12.5, "category": "Food", "date": "2026-11-16", "note": "..."}` |
| `DELETE` | `/api/expenses/{id}` | Delete one |
| `GET` | `/api/summary?month=YYYY-MM` | `{month, total, count, by_category}` |
| `GET` | `/api/categories` | The allowed category list |

## Example session (real output)

```bash
curl -X POST http://localhost:8000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 12.50, "category": "Food", "date": "2026-11-16", "note": "Groceries"}'
```

```json
{"id":1,"amount":12.5,"category":"Food","date":"2026-11-16","note":"Groceries"}
```

```bash
curl -X POST http://localhost:8000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 45.00, "category": "Transport", "date": "2026-11-10", "note": "Compass card"}'

curl "http://localhost:8000/api/summary?month=2026-11"
```

```json
{"month":"2026-11","total":57.5,"count":2,"by_category":{"Transport":45.0,"Food":12.5}}
```

```bash
curl "http://localhost:8000/api/expenses?category=Food&month=2026-11"
```

```json
[{"id":1,"amount":12.5,"category":"Food","date":"2026-11-16","note":"Groceries"}]
```

An invalid category is rejected:

```bash
curl -X POST http://localhost:8000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 5, "category": "Yachts", "date": "2026-11-16"}'
```

```json
{"detail":"category must be one of: Food, Transport, Housing, Entertainment, Health, Shopping, Other"}
```

## Data

Expenses are stored in `expenses.db` (SQLite) in the project folder, created automatically on first run.
