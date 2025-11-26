import mysql.connector
from mysql.connector import errorcode

DB_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'voluntariado',
    'raise_on_warnings': True
}

def get_connection(use_database=True):
    cfg = DB_CONFIG.copy()
    if not use_database:
        cfg.pop('database', None)
    return mysql.connector.connect(**cfg)
