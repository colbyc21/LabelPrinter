from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.services.printer import get_printer, send_zpl
from app.services.zpl import generate_labels

bp = Blueprint("adhoc", __name__)


@bp.route("/")
def search():
    term = request.args.get("q", "").strip()
    results = []
    source = None

    if term:
        from app.services import db2
        try:
            results = db2.search_customers(term)
            if results:
                source = "vbatch_labels"
            else:
                results = db2.search_oneoff_customers(term)
                if results:
                    source = "oneoff"
        except Exception as e:
            flash(f"Database error: {e}", "danger")

        if not results:
            flash("No customers found.", "warning")

    return render_template(
        "adhoc/search.html", results=results, source=source, term=term
    )


@bp.route("/print", methods=["POST"])
def print_labels():
    printer_name = session.get("printer")
    if not printer_name:
        flash("No printer selected.", "danger")
        return redirect(url_for("adhoc.search"))

    printer = get_printer(printer_name)
    if not printer:
        flash("Selected printer not found.", "danger")
        return redirect(url_for("adhoc.search"))

    source = request.form.get("source", "")
    selected = request.form.getlist("selected")
    term = request.form.get("term", "")

    if not selected:
        flash("No labels selected.", "warning")
        return redirect(url_for("adhoc.search", q=term))

    from app.services import db2
    try:
        if source == "vbatch_labels":
            all_results = db2.search_customers(term)
        else:
            all_results = db2.search_oneoff_customers(term)
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for("adhoc.search", q=term))

    # Build lookup by unique key
    zpl_all = ""
    label_count = 0

    for result in all_results:
        if source == "vbatch_labels":
            key = str(result.get("INVOICE_NO", ""))
        else:
            key = str(result.get("CUSTOMER_NO", ""))

        if key in selected:
            # Check for quantity override
            qty_key = f"qty_{key}"
            qty = request.form.get(qty_key)
            if qty and qty.isdigit() and int(qty) > 0:
                total = int(qty)
            elif source == "vbatch_labels":
                total = int(result.get("LABELS", 1) or 1)
            else:
                total = 1

            zpl_all += generate_labels(result, total_labels=total)
            label_count += total

    if not zpl_all:
        flash("No matching labels to print.", "warning")
        return redirect(url_for("adhoc.search", q=term))

    try:
        send_zpl(printer["ip"], zpl_all)
        flash(f"Sent {label_count} label(s) to {printer_name}.", "success")
    except Exception as e:
        flash(f"Print error: {e}", "danger")

    return redirect(url_for("adhoc.search", q=term))
