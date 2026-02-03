import functools
import os

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.services.printer import get_printers, add_printer, update_printer, delete_printer

bp = Blueprint("admin", __name__)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")


def admin_required(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin.printers"))
        flash("Incorrect password.", "danger")
    return render_template("admin/login.html")


@bp.route("/logout")
def logout():
    session.pop("admin", None)
    flash("Logged out of admin.", "success")
    return redirect(url_for("main.index"))


@bp.route("/printers")
@admin_required
def printers():
    return render_template("admin/printers.html", printers=get_printers())


@bp.route("/printers/add", methods=["POST"])
@admin_required
def printers_add():
    name = request.form.get("name", "").strip()
    ip = request.form.get("ip", "").strip()

    if not name or not ip:
        flash("Name and IP are required.", "danger")
    else:
        add_printer(name, ip)
        flash(f"Printer '{name}' added.", "success")

    return redirect(url_for("admin.printers"))


@bp.route("/printers/edit", methods=["POST"])
@admin_required
def printers_edit():
    old_name = request.form.get("old_name", "").strip()
    name = request.form.get("name", "").strip()
    ip = request.form.get("ip", "").strip()

    if not name or not ip:
        flash("Name and IP are required.", "danger")
    else:
        update_printer(old_name, name, ip)
        flash(f"Printer '{name}' updated.", "success")

    return redirect(url_for("admin.printers"))


@bp.route("/printers/delete", methods=["POST"])
@admin_required
def printers_delete():
    name = request.form.get("name", "").strip()
    if name:
        delete_printer(name)
        flash(f"Printer '{name}' deleted.", "success")

    return redirect(url_for("admin.printers"))
