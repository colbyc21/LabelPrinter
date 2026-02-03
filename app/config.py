import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

PRINTERS_FILE = os.path.join(BASE_DIR, "printers.json")

# DB2 for iSeries connection via individual .env variables
DB2_CONNECTION_STRING = (
    "DRIVER={IBM i Access ODBC Driver};"
    f"SYSTEM={os.environ.get('DB2_SYSTEM', '')};"
    f"UID={os.environ.get('DB2_UID', '')};"
    f"PWD={os.environ.get('DB2_PWD', '')};"
)

# Zebra printer TCP port
PRINTER_PORT = 9100
PRINTER_TIMEOUT = 5  # seconds
