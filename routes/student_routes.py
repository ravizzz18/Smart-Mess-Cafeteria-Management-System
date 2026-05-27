import io
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
import qrcode
from database.db import fetch_all, fetch_one, execute, get_connection

student_bp = Blueprint("student", __name__, template_folder="../templates")


def student_required():
    if session.get("role") != "student":
        flash("Please login as student.", "warning")
        return False
    return True


@student_bp.route("/student/dashboard")
def dashboard():
    if not student_required():
        return redirect(url_for("auth.student_login"))
    menu_items = fetch_all(
        "SELECT * FROM menu WHERE available_date = CURDATE() ORDER BY meal_type"
    )
    return render_template("student/dashboard.html", menu_items=menu_items)


@student_bp.route("/student/menu")
def menu():
    if not student_required():
        return redirect(url_for("auth.student_login"))
    menu_items = fetch_all("SELECT * FROM menu ORDER BY available_date DESC")
    return render_template("student/menu.html", menu_items=menu_items)


@student_bp.route("/student/order", methods=["POST"])
def place_order():
    if not student_required():
        return redirect(url_for("auth.student_login"))

    menu_id = request.form.get("menu_id")
    quantity = int(request.form.get("quantity", "1"))

    menu_item = fetch_one("SELECT * FROM menu WHERE menu_id = %s", (menu_id,))
    if not menu_item:
        flash("Menu item not found.", "danger")
        return redirect(url_for("student.dashboard"))

    inventory = fetch_one(
        "SELECT * FROM inventory WHERE item_name = %s", (menu_item["item_name"],)
    )
    if inventory and inventory["stock_quantity"] < quantity:
        flash("Insufficient stock for this item.", "warning")
        return redirect(url_for("student.dashboard"))

    total_amount = float(menu_item["price"]) * quantity

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (student_id, menu_id, quantity, total_amount) VALUES (%s, %s, %s, %s)",
            (session["student_id"], menu_id, quantity, total_amount),
        )
        order_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO payments (order_id, amount, payment_mode, payment_status) VALUES (%s, %s, %s, %s)",
            (order_id, total_amount, "UPI", "Paid"),
        )

    flash("Order placed successfully.", "success")
    return redirect(url_for("student.order_confirmation", order_id=order_id))


@student_bp.route("/student/order/<int:order_id>/confirmation")
def order_confirmation(order_id):
    if not student_required():
        return redirect(url_for("auth.student_login"))
    order = fetch_one(
        "SELECT o.*, m.item_name FROM orders o JOIN menu m ON o.menu_id = m.menu_id WHERE o.order_id = %s",
        (order_id,),
    )
    return render_template("student/order_confirm.html", order=order)


@student_bp.route("/student/orders")
def order_history():
    if not student_required():
        return redirect(url_for("auth.student_login"))
    orders = fetch_all(
        "SELECT o.*, m.item_name FROM orders o JOIN menu m ON o.menu_id = m.menu_id WHERE o.student_id = %s ORDER BY o.order_time DESC",
        (session["student_id"],),
    )
    return render_template("student/orders.html", orders=orders)


@student_bp.route("/student/order/<int:order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    if not student_required():
        return redirect(url_for("auth.student_login"))
    execute(
        "UPDATE orders SET order_status = %s WHERE order_id = %s AND student_id = %s",
        ("Cancelled", order_id, session["student_id"]),
    )
    execute(
        "UPDATE payments SET payment_status = %s WHERE order_id = %s",
        ("Refunded", order_id),
    )
    flash("Order cancelled.", "info")
    return redirect(url_for("student.order_history"))


@student_bp.route("/student/payments")
def payment_history():
    if not student_required():
        return redirect(url_for("auth.student_login"))
    payments = fetch_all(
        "SELECT p.*, m.item_name FROM payments p JOIN orders o ON p.order_id = o.order_id JOIN menu m ON o.menu_id = m.menu_id WHERE o.student_id = %s ORDER BY p.payment_time DESC",
        (session["student_id"],),
    )
    return render_template("student/payments.html", payments=payments)


@student_bp.route("/student/feedback", methods=["GET", "POST"])
def feedback():
    if not student_required():
        return redirect(url_for("auth.student_login"))
    menu_items = fetch_all("SELECT * FROM menu ORDER BY available_date DESC")
    if request.method == "POST":
        menu_id = request.form.get("menu_id")
        rating = int(request.form.get("rating", "5"))
        comments = request.form.get("comments", "").strip()
        execute(
            "INSERT INTO feedback (student_id, menu_id, rating, comments) VALUES (%s, %s, %s, %s)",
            (session["student_id"], menu_id, rating, comments),
        )
        flash("Feedback submitted. Thank you.", "success")
        return redirect(url_for("student.feedback"))
    return render_template("student/feedback.html", menu_items=menu_items)


@student_bp.route("/student/order/<int:order_id>/qr")
def order_qr(order_id):
    if not student_required():
        return redirect(url_for("auth.student_login"))
    payload = f"ORDER:{order_id}|STUDENT:{session['student_id']}|TIME:{datetime.utcnow().isoformat()}"
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")
