import os
from werkzeug.security import generate_password_hash
from database.db import execute, fetch_one


def seed_admin():
    admin = fetch_one("SELECT admin_id FROM admin WHERE username = %s", ("admin",))
    if not admin:
        execute(
            "INSERT INTO admin (username, password) VALUES (%s, %s)",
            ("admin", generate_password_hash("admin123")),
        )


def seed_student():
    student = fetch_one("SELECT student_id FROM students WHERE email = %s", ("student@example.com",))
    if not student:
        execute(
            "INSERT INTO students (name, email, password, hostel_block, phone) VALUES (%s, %s, %s, %s, %s)",
            (
                "Aarav Sharma",
                "student@example.com",
                generate_password_hash("student123"),
                "Block A",
                "9999988888",
            ),
        )


if __name__ == "__main__":
    seed_admin()
    seed_student()
    print("Seed data inserted.")
