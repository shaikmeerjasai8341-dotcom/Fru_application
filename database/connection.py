import pyodbc

def get_connection():
    conn = pyodbc.connect(
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=DESKTOP-CTVRDKH\\SQLEXPRESS;"
        "Database=FRU_APLICATION;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return conn