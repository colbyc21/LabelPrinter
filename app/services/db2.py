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
        region: Optional region/department filter (e.g., 'W', 'C')

    Returns:
        List of dicts with pick list data, ordered by REGION, LOCATION
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if region:
            cursor.execute(
                "SELECT CUSTNO, INVOICE, LINENO, CUSTPO, SKU, QTY2, SIZE, "
                "DESCRIPTION, REGION, LOCATION, ORDERED, SHIPPED "
                "FROM longmod.picks "
                "WHERE CUSTNO = ? AND TRIM(REGION) = ? "
                "ORDER BY REGION, LOCATION",
                (customer_no, region),
            )
        else:
            cursor.execute(
                "SELECT CUSTNO, INVOICE, LINENO, CUSTPO, SKU, QTY2, SIZE, "
                "DESCRIPTION, REGION, LOCATION, ORDERED, SHIPPED "
                "FROM longmod.picks "
                "WHERE CUSTNO = ? "
                "ORDER BY REGION, LOCATION",
                (customer_no,),
            )
        columns = [desc[0] for desc in cursor.description]
        return [_strip_row(columns, row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_pick_list_regions(customer_no):
    """Get distinct regions with pick list items for a customer."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT TRIM(REGION) AS REGION "
            "FROM longmod.picks "
            "WHERE CUSTNO = ? "
            "ORDER BY REGION",
            (customer_no,),
        )
        return [row.REGION for row in cursor.fetchall()]
    finally:
        conn.close()
