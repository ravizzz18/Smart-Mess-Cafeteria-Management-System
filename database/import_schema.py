import os
import mysql.connector
from mysql.connector import Error

SQL_FILE = os.path.join(os.path.dirname(__file__), 'schema.sql')

config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': int(os.environ.get('DB_PORT', '3306')),
}

print('Using DB config:', {k: v for k, v in config.items() if k != 'password'})

if not os.path.exists(SQL_FILE):
    print('schema.sql not found at', SQL_FILE)
    raise SystemExit(1)

with open(SQL_FILE, 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    # mysql-connector can execute multi statements
    for result in cursor.execute(sql, multi=True):
        if result.with_rows:
            print('Rows produced by statement:', result.statement)
            print(result.fetchall())
        else:
            print('Executed:', result.statement)
    conn.commit()
    print('Schema import completed successfully.')
except Error as e:
    print('Error importing schema:', e)
    raise
finally:
    try:
        cursor.close()
        conn.close()
    except Exception:
        pass
