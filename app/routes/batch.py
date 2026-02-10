from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.services.printer import get_printer, send_zpl
from app.services.zpl import generate_labels, generate_pick_list_labels

bp = Blueprint("batch", __name__)


@bp.route("/")
def select_route():
    from app.services import db2
    try:
        combos = db2.get_route_departments()
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        combos = []

    # Group by route for display
    routes = {}
    for c in combos:
        routes.setdefault(c["ROUTE"], []).append(c["PICK_AREA"])

    return render_template("batch/select_route.html", routes=routes)


@bp.route("/<route>")
def review_labels(route):
    dept = request.args.get("dept", "")
    from app.services import db2
    try:
        customers = db2.get_customers_by_route_dept(route, dept or None)
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        customers = []

    if not customers:
        flash(f"No orders found for route {route}.", "warning")

    # Calculate labels for customer 20815 from picks table (per invoice)
    labels_20815_by_invoice = None
    for cust in customers:
        if str(cust.get("CUSTOMER_NO", "")).strip() == "20815":
            if labels_20815_by_invoice is None:
                try:
                    labels_20815_by_invoice = db2.get_label_counts_for_20815_by_invoice(20815)
                except Exception:
                    labels_20815_by_invoice = {}
            invoice_no = str(cust.get("INVOICE_NO", "")).strip()
            cust["LABELS"] = labels_20815_by_invoice.get(invoice_no, 1)

    return render_template(
        "batch/review_labels.html", customers=customers, route=route, dept=dept
    )


@bp.route("/print", methods=["POST"])
def print_labels():
    printer_name = session.get("printer")
    if not printer_name:
        flash("No printer selected.", "danger")
        return redirect(url_for("batch.select_route"))

    printer = get_printer(printer_name)
    if not printer:
        flash("Selected printer not found.", "danger")
        return redirect(url_for("batch.select_route"))

    selected = request.form.getlist("selected")
    if not selected:
        flash("No labels selected.", "warning")
        return redirect(request.referrer or url_for("batch.select_route"))

    route = request.form.get("route", "")
    dept = request.form.get("dept", "")

    from app.services import db2
    try:
        customers = db2.get_customers_by_route_dept(route, dept or None)
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for("batch.select_route"))

    # Filter to selected rows and build ZPL
    # Use index-based keys since same INVOICE_NO can appear for multiple departments
    selected_set = set(selected)
    zpl_all = ""
    label_count = 0

    # For customer 20815, calculate labels from picks table (per invoice)
    labels_20815_by_invoice = None

    for idx, cust in enumerate(customers):
        if str(idx) in selected_set:
            cust_no = str(cust.get("CUSTOMER_NO", "")).strip()
            if cust_no == "20815":
                # Calculate labels from picks: M-Z=1 per unit, others=1 per 6 units
                if labels_20815_by_invoice is None:
                    try:
                        labels_20815_by_invoice = db2.get_label_counts_for_20815_by_invoice(20815)
                    except Exception:
                        labels_20815_by_invoice = {}
                invoice_no = str(cust.get("INVOICE_NO", "")).strip()
                labels = labels_20815_by_invoice.get(invoice_no, 1)
            else:
                labels = int(cust.get("LABELS", 1) or 1)
            zpl_all += generate_labels(cust, total_labels=labels)
            label_count += labels

    if not zpl_all:
        flash("No matching labels to print.", "warning")
        return redirect(url_for("batch.review_labels", route=route, dept=dept))

    try:
        send_zpl(printer["ip"], zpl_all)
        flash(f"Sent {label_count} label(s) to {printer_name}.", "success")
    except Exception as e:
        flash(f"Print error: {e}", "danger")

    return redirect(url_for("batch.review_labels", route=route, dept=dept))


@bp.route("/print-pick-list", methods=["POST"])
def print_pick_list():
    """Print pick list labels for customer 20815."""
    printer_name = session.get("printer")
    if not printer_name:
        flash("No printer selected.", "danger")
        return redirect(url_for("batch.select_route"))

    printer = get_printer(printer_name)
    if not printer:
        flash("Selected printer not found.", "danger")
        return redirect(url_for("batch.select_route"))

    route = request.form.get("route", "")
    dept = request.form.get("dept", "")

    from app.services import db2

    # Get all regions for customer 20815 and print pick lists
    try:
        regions = db2.get_pick_list_regions(20815)
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for("batch.review_labels", route=route, dept=dept))

    if not regions:
        flash("No pick list items found for customer 20815.", "warning")
        return redirect(url_for("batch.review_labels", route=route, dept=dept))

    zpl_all = ""
    label_count = 0

    for region in regions:
        try:
            items = db2.get_pick_list(20815, region)
            if items:
                zpl_all += generate_pick_list_labels(items, region)
                # Count labels (12 items per label)
                label_count += (len(items) + 11) // 12
        except Exception as e:
            flash(f"Error getting pick list for region {region}: {e}", "danger")

    if not zpl_all:
        flash("No pick list labels to print.", "warning")
        return redirect(url_for("batch.review_labels", route=route, dept=dept))

    try:
        send_zpl(printer["ip"], zpl_all)
        flash(f"Sent {label_count} pick list label(s) to {printer_name}.", "success")
    except Exception as e:
        flash(f"Print error: {e}", "danger")

    return redirect(url_for("batch.review_labels", route=route, dept=dept))
