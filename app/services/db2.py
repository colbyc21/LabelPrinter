import pyodbc  # requires ibm-iaccess ODBC driver on the system
from app.config import DB2_CONNECTION_STRING


def get_connection():
    return pyodbc.connect(DB2_CONNECTION_STRING)


def _strip_row(columns, row):
    """Strip trailing whitespace from string values in a row."""
    return {
        col: val.strip() if isinstance(val, str) else val
        for col, val in zip(columns, row)
    }


def get_route_departments():
    """Get distinct route/department combos from picked orders."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT TRIM(ROUTE) AS ROUTE, TRIM(PICK_AREA) AS PICK_AREA "
            "FROM longmod.vbatch_labels "
            "ORDER BY ROUTE, PICK_AREA"
        )
        return [
            {"ROUTE": row.ROUTE, "PICK_AREA": row.PICK_AREA}
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()


def get_customers_by_route_dept(route, dept=None):
    """Get customers for a route (optionally filtered by department).

    Results are ordered by PICK_AREA then STOP so each department
    prints in stop-ascending order before the next department starts.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if dept:
            cursor.execute(
                "SELECT INVOICE_NO, CUSTOMER_NO, CUSTOMER, ADDRESS, CITY, STATE, "
                "ZIP, PO_NUM, ROUTE, STOP, PICK_AREA, LABELS "
                "FROM longmod.vbatch_labels "
                "WHERE TRIM(ROUTE) = ? AND TRIM(PICK_AREA) = ? "
                "ORDER BY PICK_AREA, STOP",
                (route, dept),
            )
        else:
            cursor.execute(
                "SELECT INVOICE_NO, CUSTOMER_NO, CUSTOMER, ADDRESS, CITY, STATE, "
                "ZIP, PO_NUM, ROUTE, STOP, PICK_AREA, LABELS "
                "FROM longmod.vbatch_labels "
                "WHERE TRIM(ROUTE) = ? "
                "ORDER BY PICK_AREA, STOP",
                (route,),
            )
        columns = [desc[0] for desc in cursor.description]
        return [_strip_row(columns, row) for row in cursor.fetchall()]
    finally:
        conn.close()


def search_customers(term):
    """Search vbatch_labels by customer name or number."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        like_term = f"%{term.upper()}%"
        if term.isdigit():
            cursor.execute(
                "SELECT INVOICE_NO, CUSTOMER_NO, CUSTOMER, ADDRESS, CITY, STATE, "
                "ZIP, PO_NUM, ROUTE, STOP, PICK_AREA, LABELS "
                "FROM longmod.vbatch_labels "
                "WHERE UPPER(CUSTOMER) LIKE ? OR CUSTOMER_NO = ? "
                "ORDER BY ROUTE, STOP",
                (like_term, int(term)),
            )
        else:
            cursor.execute(
                "SELECT INVOICE_NO, CUSTOMER_NO, CUSTOMER, ADDRESS, CITY, STATE, "
                "ZIP, PO_NUM, ROUTE, STOP, PICK_AREA, LABELS "
                "FROM longmod.vbatch_labels "
                "WHERE UPPER(CUSTOMER) LIKE ? "
                "ORDER BY ROUTE, STOP",
                (like_term,),
            )
        columns = [desc[0] for desc in cursor.description]
        return [_strip_row(columns, row) for row in cursor.fetchall()]
    finally:
        conn.close()


def search_oneoff_customers(term):
    """Fallback search in VONEOFF_LASTSTOP for ad hoc labels."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        like_term = f"%{term.upper()}%"
        if term.isdigit():
            cursor.execute(
                "SELECT CUSTOMER_NO, CUSTOMER, ADDRESS, CITY, STATE_CD, ZIP, "
                "ROUTE, STOP "
                "FROM longmod.VONEOFF_LASTSTOP "
                "WHERE UPPER(CUSTOMER) LIKE ? OR CUSTOMER_NO = ? "
                "ORDER BY CUSTOMER",
                (like_term, int(term)),
            )
        else:
            cursor.execute(
                "SELECT CUSTOMER_NO, CUSTOMER, ADDRESS, CITY, STATE_CD, ZIP, "
                "ROUTE, STOP "
                "FROM longmod.VONEOFF_LASTSTOP "
                "WHERE UPPER(CUSTOMER) LIKE ? "
                "ORDER BY CUSTOMER",
                (like_term,),
            )
        columns = [desc[0] for desc in cursor.description]
        return [_strip_row(columns, row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_pick_list(customer_no, region=None):
    """Get pick list items from longmod.picks for a customer.

    Args:
        customer_no: Customer number (e.g., 20815)
        region: Optional region/department filter (e.g., 'MW' for Main Warehouse M-Z)

    Returns:
        List of dicts with pick list data, ordered by derived region, LOCATION.
        Region is derived from first letter of LOCATION (slot) since Route 10
        defaults REGION to 'CC' instead of the actual pick area.
        Locations starting with M-Z are grouped as 'MW' (Main Warehouse).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Derive region from first letter of LOCATION
        # M-Z locations grouped as 'MW' (Main Warehouse)
        region_expr = (
            "CASE WHEN SUBSTR(LOCATION, 1, 1) >= 'M' "
            "THEN 'MW' ELSE SUBSTR(LOCATION, 1, 1) END"
        )
        if region:
            if region == "MW":
                cursor.execute(
                    f"SELECT CUSTNO, INVOICE, LINENO, CUSTPO, SKU, QTY2, SIZE, "
                    f"DESCRIPTION, {region_expr} AS REGION, LOCATION, ORDERED, SHIPPED "
                    f"FROM longmod.picks "
                    f"WHERE CUSTNO = ? AND SUBSTR(LOCATION, 1, 1) >= 'M' "
                    f"ORDER BY LOCATION",
                    (customer_no,),
                )
            else:
                cursor.execute(
                    f"SELECT CUSTNO, INVOICE, LINENO, CUSTPO, SKU, QTY2, SIZE, "
                    f"DESCRIPTION, {region_expr} AS REGION, LOCATION, ORDERED, SHIPPED "
                    f"FROM longmod.picks "
                    f"WHERE CUSTNO = ? AND SUBSTR(LOCATION, 1, 1) = ? "
                    f"ORDER BY LOCATION",
                    (customer_no, region),
                )
        else:
            cursor.execute(
                f"SELECT CUSTNO, INVOICE, LINENO, CUSTPO, SKU, QTY2, SIZE, "
                f"DESCRIPTION, {region_expr} AS REGION, LOCATION, ORDERED, SHIPPED "
                f"FROM longmod.picks "
                f"WHERE CUSTNO = ? "
                f"ORDER BY {region_expr}, LOCATION",
                (customer_no,),
            )
        columns = [desc[0] for desc in cursor.description]
        return [_strip_row(columns, row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_label_counts_for_20815_by_invoice(customer_no):
    """Calculate label counts for customer 20815 by invoice based on picks.

    Rules:
    - M-Z locations (Main Warehouse): 1 label per unit shipped
    - All other locations: 1 label per 6 units shipped (rounded up)

    Returns:
        Dict mapping invoice number to label count.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Calculate labels per invoice: M-Z = 1 per unit, others = ceil(shipped/6)
        cursor.execute(
            "SELECT INVOICE, "
            "SUM(CASE WHEN SUBSTR(LOCATION, 1, 1) >= 'M' THEN SHIPPED "
            "ELSE CEILING(CAST(SHIPPED AS DECIMAL(10,2)) / 6) END) AS LABEL_COUNT "
            "FROM longmod.picks "
            "WHERE CUSTNO = ? "
            "GROUP BY INVOICE",
            (customer_no,),
        )
        return {
            str(row.INVOICE).strip(): int(row.LABEL_COUNT or 1)
            for row in cursor.fetchall()
        }
    finally:
        conn.close()


def get_pick_list_regions(customer_no):
    """Get distinct regions with pick list items for a customer.

    Region is derived from first letter of LOCATION (slot).
    Locations starting with M-Z are grouped as 'MW' (Main Warehouse).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT "
            "CASE WHEN SUBSTR(LOCATION, 1, 1) >= 'M' "
            "THEN 'MW' ELSE SUBSTR(LOCATION, 1, 1) END AS REGION "
            "FROM longmod.picks "
            "WHERE CUSTNO = ? "
            "ORDER BY REGION",
            (customer_no,),
        )
        return [row.REGION for row in cursor.fetchall()]
    finally:
        conn.close()
