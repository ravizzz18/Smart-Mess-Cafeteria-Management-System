from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import fetch_one, execute

auth_bp = Blueprint("auth", __name__, template_folder="../templates")


def verify_password(stored_password, provided_password):
    if stored_password.startswith("pbkdf2:") or stored_password.startswith("scrypt:"):
        return check_password_hash(stored_password, provided_password)
    return stored_password == provided_password


@auth_bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        student = fetch_one("SELECT * FROM students WHERE email = %s", (email,))
        if not student or not verify_password(student["password"], password):
            flash("Invalid student credentials.", "danger")
            return redirect(url_for("auth.student_login"))
        session.clear()
        session["student_id"] = student["student_id"]
        session["role"] = "student"
        flash("Welcome back.", "success")
        return redirect(url_for("student.dashboard"))
    return render_template("auth/login_student.html")


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = fetch_one("SELECT * FROM admin WHERE username = %s", (username,))
        if not admin or not verify_password(admin["password"], password):
            flash("Invalid admin credentials.", "danger")
            return redirect(url_for("auth.admin_login"))
        session.clear()
        session["admin_id"] = admin["admin_id"]
        session["role"] = "admin"
        flash("Admin login successful.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("auth/login_admin.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def student_signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        hostel_block = request.form.get("hostel_block", "").strip()
        phone = request.form.get("phone", "").strip()

        if not all([name, email, password, hostel_block, phone]):
            flash("Please fill in all required fields.", "warning")
            return redirect(url_for("auth.student_signup"))

        existing = fetch_one("SELECT student_id FROM students WHERE email = %s", (email,))
        if existing:
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.student_signup"))

        execute(
            "INSERT INTO students (name, email, password, hostel_block, phone) VALUES (%s, %s, %s, %s, %s)",
            (name, email, generate_password_hash(password), hostel_block, phone),
        )
        flash("Signup successful. Please login.", "success")
        return redirect(url_for("auth.student_login"))

    return render_template("auth/signup.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.student_login"))
