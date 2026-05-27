<<<<<<< HEAD
# Smart Mess & Cafeteria Management System

A professional DBMS-focused cafeteria management system built with Flask + MySQL. The project prioritizes strong database design, SQL operations, and admin monitoring dashboards.

## Overview

This is a full-stack educational project demonstrating a DBMS-focused cafeteria/mess management system built with Flask and MySQL. It emphasizes clean relational design (up to 3NF), triggers, stored procedures, views, transactions, and practical admin/student workflows.

## Features

- Student module: signup/login, view menu, order meals, order history, payments, feedback
- Admin module: dashboard analytics, menu CRUD, orders, payments, inventory, feedback, reports
- DBMS concepts: normalized schema, joins, views, triggers, stored procedures, transactions
- QR order token generation, Chart.js analytics, CSV/PDF exports

## Tech Stack

- Frontend: HTML5, CSS3, Bootstrap 5, JavaScript
- Backend: Python Flask
- Database: MySQL

## Quick Start (Windows)

1. Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start MySQL using Docker (recommended):

```powershell
docker run --name smart-mess-mysql -e MYSQL_ROOT_PASSWORD=ChangeMe123! -e MYSQL_DATABASE=smart_mess_db -p 3306:3306 -d mysql:8.0 --default-authentication-plugin=mysql_native_password
docker cp database/schema.sql smart-mess-mysql:/schema.sql
docker exec -i smart-mess-mysql mysql -u root -p'ChangeMe123!' smart_mess_db < /schema.sql
```

4. Seed the database (optional):

```powershell
python -m database.seed
```

5. Set environment variables (recommended):

```powershell
$env:DB_HOST='localhost'
$env:DB_USER='root'
$env:DB_PASSWORD='ChangeMe123!'
$env:DB_NAME='smart_mess_db'
$env:DB_PORT='3306'
$env:FLASK_SECRET_KEY='change_this'
```

6. Run the Flask app:

```powershell
.\.venv\Scripts\python.exe app.py
```

7. Open http://127.0.0.1:5000 in your browser.

## Default Accounts

- Admin: `admin` / `admin123`
- Student: `student@example.com` / `student123`

## DBMS Highlights

- Views: `order_summary`, `payment_summary`
- Trigger: `trg_reduce_inventory` reduces stock after orders
- Stored procedure: `daily_sales_report(date)`

Example:

```sql
CALL daily_sales_report(CURDATE());
```

## Project Structure

```
app.py
requirements.txt
routes/
models/
database/
static/
templates/
```

## Notes & Next Steps

- For production, remove the development DB password fallback in `database/db.py` and use secure secrets management.
- Consider adding migrations (Alembic) for schema evolution.
- Tests are not included; adding automated integration tests would be a good next step.

If you'd like, I can finish pushing these commits to your GitHub repository — confirm and I'll continue.

