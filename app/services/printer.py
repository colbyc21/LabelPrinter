import json
import os
import socket

from app.config import PRINTERS_FILE, PRINTER_PORT, PRINTER_TIMEOUT


# --- JSON config CRUD ---

def _load_printers():
    if not os.path.exists(PRINTERS_FILE):
        return []
    with open(PRINTERS_FILE, "r") as f:
        return json.load(f)


def _save_printers(printers):
    with open(PRINTERS_FILE, "w") as f:
        json.dump(printers, f, indent=4)


def get_printers():
    return _load_printers()


def get_printer(name):
    for p in _load_printers():
        if p["name"] == name:
            return p
    return None


def add_printer(name, ip):
    printers = _load_printers()
    printers.append({"name": name, "ip": ip})
    _save_printers(printers)


def update_printer(old_name, name, ip):
    printers = _load_printers()
    for p in printers:
        if p["name"] == old_name:
            p["name"] = name
            p["ip"] = ip
            break
    _save_printers(printers)


def delete_printer(name):
    printers = _load_printers()
    printers = [p for p in printers if p["name"] != name]
    _save_printers(printers)


# --- TCP socket printing ---

def send_zpl(ip, zpl_data):
    """Send ZPL data to a Zebra printer via raw TCP socket on port 9100."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(PRINTER_TIMEOUT)
    try:
        sock.connect((ip, PRINTER_PORT))
        sock.sendall(zpl_data.encode("utf-8"))
    finally:
        sock.close()
