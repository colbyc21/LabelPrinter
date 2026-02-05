def generate_label(data, label_number=1, total_labels=1):
    """Generate ZPL for a single 4x6 shipping label at 203 DPI.

    Args:
        data: dict with keys: ROUTE, STOP, CUSTOMER, CITY, STATE (or STATE_CD),
              and optionally INVOICE_NO, PO_NUM, PICK_AREA, CUSTOMER_NO.
        label_number: current label number (1-based).
        total_labels: total labels for this customer/invoice.

    Returns:
        ZPL string for one label.
    """
    route = str(data.get("ROUTE", "")).strip()
    stop = str(data.get("STOP", "")).strip()
    customer = str(data.get("CUSTOMER", "")).strip()
    customer_no = str(data.get("CUSTOMER_NO", "")).strip()
    city = str(data.get("CITY", "")).strip()
    state = str(data.get("STATE") or data.get("STATE_CD") or "").strip()

    invoice = str(data.get("INVOICE_NO", "")).strip()
    po = str(data.get("PO_NUM", "")).strip()
    pick_area = str(data.get("PICK_AREA", "")).strip()

    city_state = f"{city}, {state}" if city and state else city or state

    # Customer 20815 gets PO-prominent layout
    if customer_no == "20815":
        zpl = (
            "^XA\n"
            "^CF0,80\n"
            f"^FO50,30^FDPO: {po}^FS\n"
            "^FO50,120^GB700,4,4^FS\n"
            "^CF0,100\n"
            f"^FO50,140^FDRT: {route}^FS\n"
            f"^FO400,140^FDST: {stop}^FS\n"
            "^FO50,260^GB700,4,4^FS\n"
            "^CF0,50\n"
            f"^FO50,290^FD{customer}^FS\n"
            "^CF0,40\n"
            f"^FO50,360^FD{city_state}^FS\n"
            "^FO50,420^GB700,4,4^FS\n"
            "^CF0,35\n"
            f"^FO50,450^FDInvoice: {invoice}^FS\n"
            f"^FO50,500^FDPick: {pick_area}^FS\n"
            "^XZ\n"
        )
    else:
        # Standard layout
        zpl = (
            "^XA\n"
            "^CF0,130\n"
            f"^FO50,50^FDRT: {route}^FS\n"
            f"^FO450,50^FDST: {stop}^FS\n"
            "^FO50,200^GB700,4,4^FS\n"
            "^CF0,55\n"
            f"^FO50,230^FD{customer}^FS\n"
            "^CF0,45\n"
            f"^FO50,310^FD{city_state}^FS\n"
            "^FO50,380^GB700,4,4^FS\n"
            "^CF0,35\n"
        )

        if invoice:
            zpl += f"^FO50,410^FDInvoice: {invoice}^FS\n"
        if po:
            zpl += f"^FO450,410^FDPO: {po}^FS\n"
        if pick_area:
            zpl += f"^FO50,460^FDPick: {pick_area}^FS\n"

        zpl += (
            "^FO50,520^GB700,4,4^FS\n"
            "^XZ\n"
        )

    return zpl


def generate_labels(data, total_labels=None):
    """Generate ZPL for all labels for a given row.

    Args:
        data: dict from DB query.
        total_labels: override label count (defaults to data['LABELS'] or 1).

    Returns:
        ZPL string containing all labels concatenated.
    """
    if total_labels is None:
        total_labels = int(data.get("LABELS", 1) or 1)

    parts = []
    for i in range(1, total_labels + 1):
        parts.append(generate_label(data, label_number=i, total_labels=total_labels))
    return "".join(parts)
