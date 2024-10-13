import sqlite3
import os
import threading

class DatabaseHandler:
    _local = threading.local()

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'server_config.db')
        self._local.conn = None
        self._local.cursor = None
        self.connect()
        self.create_table()

    def connect(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.cursor = self._local.conn.cursor()

    def create_table(self):
        self.connect()
        self._local.cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        self._local.cursor.execute('''
            INSERT OR IGNORE INTO server_config (key, value) VALUES
            ('NGROK_AUTH_TOKEN', ''),
            ('SHODAN_API_KEY', ''),
            ('USE_SHODAN_DATA', 'False'),
            ('SMTP_HOST', ''),
            ('SMTP_PORT', ''),
            ('SMTP_USERNAME', ''),
            ('SMTP_PASSWORD', ''),
            ('SMTP_SECURITY', 'TLS')
        ''')
        self._local.conn.commit()

    def set_value(self, key, value):
        self.connect()
        self._local.cursor.execute('''
            INSERT OR REPLACE INTO server_config (key, value)
            VALUES (?, ?)
        ''', (key, value))
        self._local.conn.commit()

    def get_value(self, key, default=None):
        self.connect()
        self._local.cursor.execute('SELECT value FROM server_config WHERE key = ?', (key,))
        result = self._local.cursor.fetchone()
        return result[0] if result else default

    def close(self):
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
            self._local.cursor = None

db = DatabaseHandler()
