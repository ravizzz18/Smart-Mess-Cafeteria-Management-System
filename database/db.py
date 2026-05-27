import os
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager


def get_db_config():
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "smart_mess_db"),
        "port": int(os.environ.get("DB_PORT", "3306")),
    }


@contextmanager
def get_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**get_db_config())
        yield conn
        conn.commit()
    except Error:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def fetch_all(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()


def fetch_one(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchone()


def execute(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return cursor.lastrowid


def execute_many(query, params_list):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
