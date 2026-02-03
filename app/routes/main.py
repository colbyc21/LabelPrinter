from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.services.printer import get_printers

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    printers = get_printers()
    return render_template("index.html", printers=printers)


@bp.route("/set-printer", methods=["POST"])
def set_printer():
    printer_name = request.form.get("printer")
    if printer_name:
        session["printer"] = printer_name
        flash(f"Printer set to {printer_name}", "success")
    return redirect(request.referrer or url_for("main.index"))


@bp.route("/test-print", methods=["POST"])
def test_print():
    from app.services.printer import get_printer, send_zpl
    from app.services.zpl import generate_label

    printer_name = session.get("printer")
    if not printer_name:
        flash("No printer selected.", "danger")
        return redirect(url_for("main.index"))

    printer = get_printer(printer_name)
    if not printer:
        flash("Selected printer not found.", "danger")
        return redirect(url_for("main.index"))

    test_data = {
        "ROUTE": "14",
        "STOP": "03",
        "CUSTOMER": "ACME WHOLESALE FOODS",
        "CITY": "DALLAS",
        "STATE": "TX",
        "INVOICE_NO": "123456",
        "PO_NUM": "PO-99887",
        "PICK_AREA": "DRY",
    }

    zpl = generate_label(test_data)
    try:
        send_zpl(printer["ip"], zpl)
        flash("Test label sent.", "success")
    except Exception as e:
        flash(f"Print error: {e}", "danger")

    return redirect(url_for("main.index"))
