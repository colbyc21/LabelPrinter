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
            "^FWN\n"  # Reset field orientation to normal
            "^PON\n"  # Print orientation normal
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
            "^FWN\n"  # Reset field orientation to normal
            "^PON\n"  # Print orientation normal
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


def generate_pick_list_labels(items, region):
    """Generate ZPL for pick list labels on 4x6 format.

    Args:
        items: List of dicts from longmod.picks query (should be pre-sorted)
        region: Department/region code (e.g., 'W', 'C', 'MW' for Main Warehouse)

    Returns:
        ZPL string for all pick list labels (multiple labels if > 12 items)
    """
    if not items:
        return ""

    # Portrait 4x6 label at 203 DPI
    # 4" = 812 dots wide, 6" = 1218 dots tall
    ROWS_PER_LABEL = 12
    labels = []

    # Display name for region
    region_name = "Main Warehouse" if region == "MW" else f"DEPT {region}"

    for page_start in range(0, len(items), ROWS_PER_LABEL):
        page_items = items[page_start:page_start + ROWS_PER_LABEL]
        page_num = (page_start // ROWS_PER_LABEL) + 1
        total_pages = (len(items) + ROWS_PER_LABEL - 1) // ROWS_PER_LABEL

        zpl = (
            "^XA\n"
            "^FWN\n"  # Reset field orientation to normal (no rotation)
            "^PON\n"  # Print orientation normal
            # Header at top
            "^CF0,35\n"
            f"^FO20,20^FD{region_name} PICK LIST^FS\n"
            f"^FO680,20^FD{page_num}/{total_pages}^FS\n"
            "^FO20,60^GB770,3,3^FS\n"
            # Column headers - tighter layout for 4" (812 dots)
            "^CF0,18\n"
            "^FO20,70^FDSLOT^FS\n"
            "^FO85,70^FDINV^FS\n"
            "^FO150,70^FDORD^FS\n"
            "^FO185,70^FDSHP^FS\n"
            "^FO220,70^FDPO^FS\n"
            "^FO330,70^FDLN^FS\n"
            "^FO360,70^FDDESCRIPTION^FS\n"
            "^FO590,70^FDPK^FS\n"
            "^FO630,70^FDSIZE^FS\n"
            "^FO20,90^GB770,2,2^FS\n"
            # Data rows
            "^CF0,18\n"
        )

        y = 100  # Starting vertical position for first data row
        row_height = 24
        for item in page_items:
            slot = str(item.get("LOCATION", "")).strip()[:7]
            invoice = str(item.get("INVOICE", "")).strip()[:6]
            ordered = str(int(item.get("ORDERED", 0) or 0))
            shipped = str(int(item.get("SHIPPED", 0) or 0))
            custpo = str(item.get("CUSTPO", "")).strip()[:10]
            lineno = str(int(item.get("LINENO", 0) or 0))
            desc = str(item.get("DESCRIPTION", "")).strip()[:18]
            pk = str(item.get("QTY2", "")).strip()[:4]
            size = str(item.get("SIZE", "")).strip()[:10]

            zpl += (
                f"^FO20,{y}^FD{slot}^FS\n"
                f"^FO85,{y}^FD{invoice}^FS\n"
                f"^FO150,{y}^FD{ordered}^FS\n"
                f"^FO185,{y}^FD{shipped}^FS\n"
                f"^FO220,{y}^FD{custpo}^FS\n"
                f"^FO330,{y}^FD{lineno}^FS\n"
                f"^FO360,{y}^FD{desc}^FS\n"
                f"^FO590,{y}^FD{pk}^FS\n"
                f"^FO630,{y}^FD{size}^FS\n"
            )
            y += row_height

        zpl += "^XZ\n"
        labels.append(zpl)

    return "".join(labels)
