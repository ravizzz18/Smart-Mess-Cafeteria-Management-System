from datetime import date, timedelta
import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from fpdf import FPDF
from database.db import fetch_all, fetch_one, execute

admin_bp = Blueprint("admin", __name__, template_folder="../templates")


def admin_required():
    if session.get("role") != "admin":
        flash("Please login as admin.", "warning")
        return False
    return True


@admin_bp.route("/admin/dashboard")
def dashboard():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    totals = fetch_one("SELECT COUNT(*) AS total_orders, SUM(total_amount) AS total_revenue FROM orders")
    pending = fetch_one("SELECT COUNT(*) AS pending_orders FROM orders WHERE order_status = 'Pending'")
    most_ordered = fetch_one(
        "SELECT m.item_name, SUM(o.quantity) AS total_qty FROM orders o JOIN menu m ON o.menu_id = m.menu_id GROUP BY m.item_name ORDER BY total_qty DESC LIMIT 1"
    )
    recent_orders = fetch_all("SELECT * FROM order_summary ORDER BY order_time DESC LIMIT 10")
    students = fetch_all("SELECT * FROM students ORDER BY created_at DESC LIMIT 10")
    inventory = fetch_all("SELECT * FROM inventory ORDER BY stock_quantity ASC")
    payments = fetch_all("SELECT * FROM payment_summary ORDER BY payment_time DESC LIMIT 10")

    revenue_data = fetch_all(
        "SELECT DATE(order_time) AS order_date, SUM(total_amount) AS daily_revenue FROM orders WHERE order_time >= %s GROUP BY DATE(order_time) ORDER BY order_date",
        ((date.today() - timedelta(days=6)).isoformat(),),
    )

    return render_template(
        "admin/dashboard.html",
        totals=totals,
        pending=pending,
        most_ordered=most_ordered,
        recent_orders=recent_orders,
        pdf.ln(4)
        pdf.set_auto_page_break(True, margin=15)
        usable_w = pdf.w - pdf.l_margin - pdf.r_margin
        font_family = getattr(pdf, "font_family", "Arial")
        for row in orders[:50]:
            line = (
                f"#{row['order_id']} {row['student_name']} - {row['item_name']} "
                f"x{row['quantity']} = {row['total_amount']} ({row['order_status']})"
            )
            try:
                pdf.set_x(pdf.l_margin)
            except Exception:
                pass

            try:
                pdf.multi_cell(usable_w, 8, txt=line)
            except Exception as exc:
                from fpdf.errors import FPDFException

                if isinstance(exc, FPDFException):
                    orig_size = getattr(pdf, "font_size_pt", 12)
                    success = False
                    for new_size in range(int(orig_size) - 1, 5, -1):
                        pdf.set_font(font_family, size=new_size)
                        try:
                            pdf.set_x(pdf.l_margin)
                            pdf.multi_cell(usable_w, 8, txt=line)
                            success = True
                            break
                        except FPDFException:
                            continue

                    if not success:
                        import textwrap

                        char_w = pdf.get_string_width("M") or 1
                        approx_chars = max(1, int(usable_w / char_w))
                        wrapped = textwrap.wrap(line, width=approx_chars, break_long_words=True, break_on_hyphens=True)
                        for wl in wrapped:
                            pdf.set_x(pdf.l_margin)
                            pdf.multi_cell(usable_w, 8, txt=wl)

                    try:
                        pdf.set_font(font_family, size=orig_size)
                    except Exception:
                        pass
                else:
                    raise
        return redirect(url_for("admin.menu_list"))
    return render_template("admin/menu_form.html", item=item)


@admin_bp.route("/admin/menu/<int:menu_id>/delete", methods=["POST"])
def menu_delete(menu_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    execute("DELETE FROM menu WHERE menu_id = %s", (menu_id,))
    flash("Menu item deleted.", "info")
    return redirect(url_for("admin.menu_list"))


@admin_bp.route("/admin/orders")
def orders_list():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    status = request.args.get("status", "")
    student = request.args.get("student", "")
    query = "SELECT * FROM order_summary WHERE 1=1"
    params = []
    if status:
        query += " AND order_status = %s"
        params.append(status)
    if student:
        query += " AND student_name LIKE %s"
        params.append(f"%{student}%")
    query += " ORDER BY order_time DESC"
    orders = fetch_all(query, tuple(params))
    return render_template("admin/orders.html", orders=orders, status=status, student=student)


@admin_bp.route("/admin/orders/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    status = request.form.get("order_status")
    execute("UPDATE orders SET order_status = %s WHERE order_id = %s", (status, order_id))
    flash("Order status updated.", "success")
    return redirect(url_for("admin.orders_list"))


@admin_bp.route("/admin/students")
def students_list():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    students = fetch_all("SELECT * FROM students ORDER BY created_at DESC")
    return render_template("admin/students.html", students=students)


@admin_bp.route("/admin/payments")
def payments_list():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    payments = fetch_all("SELECT * FROM payment_summary ORDER BY payment_time DESC")
    return render_template("admin/payments.html", payments=payments)


@admin_bp.route("/admin/inventory")
def inventory_list():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    items = fetch_all("SELECT * FROM inventory ORDER BY stock_quantity ASC")
    return render_template("admin/inventory.html", items=items)


@admin_bp.route("/admin/inventory/add", methods=["GET", "POST"])
def inventory_add():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        stock_quantity = request.form.get("stock_quantity")
        supplier_name = request.form.get("supplier_name", "").strip()
        execute(
            "INSERT INTO inventory (item_name, stock_quantity, supplier_name) VALUES (%s, %s, %s)",
            (item_name, stock_quantity, supplier_name),
        )
        flash("Inventory item added.", "success")
        return redirect(url_for("admin.inventory_list"))
    return render_template("admin/inventory_form.html", item=None)


@admin_bp.route("/admin/inventory/<int:item_id>/edit", methods=["GET", "POST"])
def inventory_edit(item_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    item = fetch_one("SELECT * FROM inventory WHERE item_id = %s", (item_id,))
    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        stock_quantity = request.form.get("stock_quantity")
        supplier_name = request.form.get("supplier_name", "").strip()
        execute(
            "UPDATE inventory SET item_name = %s, stock_quantity = %s, supplier_name = %s WHERE item_id = %s",
            (item_name, stock_quantity, supplier_name, item_id),
        )
        flash("Inventory updated.", "success")
        return redirect(url_for("admin.inventory_list"))
    return render_template("admin/inventory_form.html", item=item)


@admin_bp.route("/admin/inventory/<int:item_id>/delete", methods=["POST"])
def inventory_delete(item_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    execute("DELETE FROM inventory WHERE item_id = %s", (item_id,))
    flash("Inventory item deleted.", "info")
    return redirect(url_for("admin.inventory_list"))


@admin_bp.route("/admin/feedback")
def feedback_list():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    feedback = fetch_all(
        "SELECT f.*, s.name AS student_name, m.item_name FROM feedback f JOIN students s ON f.student_id = s.student_id JOIN menu m ON f.menu_id = m.menu_id ORDER BY f.feedback_date DESC"
    )
    return render_template("admin/feedback.html", feedback=feedback)


@admin_bp.route("/admin/reports")
def reports():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))
    report_type = request.args.get("format")
    orders = fetch_all("SELECT * FROM order_summary ORDER BY order_time DESC")

    if report_type == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Order ID", "Student", "Item", "Qty", "Amount", "Status", "Time"])
        for row in orders:
            writer.writerow(
                [
                    row["order_id"],
                    row["student_name"],
                    row["item_name"],
                    row["quantity"],
                    row["total_amount"],
                    row["order_status"],
                    row["order_time"],
                ]
            )
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="orders_report.csv",
        )

    if report_type == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Orders Report", ln=True, align="C")
        pdf.ln(4)
        pdf.set_auto_page_break(True, margin=15)
<<<<<<< HEAD
        usable_w = pdf.w - pdf.l_margin - pdf.r_margin
        font_family = getattr(pdf, "font_family", "Arial")
=======
>>>>>>> d3b6d35 (Fix PDF multi_cell width issue in admin reports)
        for row in orders[:50]:
            line = (
                f"#{row['order_id']} {row['student_name']} - {row['item_name']} "
                f"x{row['quantity']} = {row['total_amount']} ({row['order_status']})"
            )
<<<<<<< HEAD
=======
            # ensure we're at the left margin so multi_cell has full horizontal space
>>>>>>> d3b6d35 (Fix PDF multi_cell width issue in admin reports)
            try:
                pdf.set_x(pdf.l_margin)
            except Exception:
                pass
<<<<<<< HEAD

            try:
                pdf.multi_cell(usable_w, 8, txt=line)
            except Exception as exc:
                from fpdf.errors import FPDFException

                if isinstance(exc, FPDFException):
                    orig_size = getattr(pdf, "font_size_pt", 12)
                    success = False
                    for new_size in range(int(orig_size) - 1, 5, -1):
                        pdf.set_font(font_family, size=new_size)
                        try:
                            pdf.set_x(pdf.l_margin)
                            pdf.multi_cell(usable_w, 8, txt=line)
                            success = True
                            break
                        except FPDFException:
                            continue

                    if not success:
                        import textwrap

                        char_w = pdf.get_string_width("M") or 1
                        approx_chars = max(1, int(usable_w / char_w))
                        wrapped = textwrap.wrap(line, width=approx_chars, break_long_words=True, break_on_hyphens=True)
                        for wl in wrapped:
                            pdf.set_x(pdf.l_margin)
                            pdf.multi_cell(usable_w, 8, txt=wl)

                    try:
                        pdf.set_font(font_family, size=orig_size)
                    except Exception:
                        pass
                else:
                    raise
=======
            pdf.multi_cell(0, 8, txt=line)
>>>>>>> d3b6d35 (Fix PDF multi_cell width issue in admin reports)
        pdf_out = pdf.output(dest="S")
        if isinstance(pdf_out, bytearray):
            pdf_bytes = bytes(pdf_out)
        elif isinstance(pdf_out, str):
            pdf_bytes = pdf_out.encode("latin-1")
        else:
            pdf_bytes = pdf_out
        buffer = io.BytesIO(pdf_bytes)
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="orders_report.pdf",
        )

    return render_template("admin/reports.html")
