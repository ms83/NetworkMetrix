import sqlite3
import time
from config import cf
    

class DB(object):
    """ Retational database interface.
        It is designed to easily allow engine change.
        Current engine: SQLite
    """

    def __init__(self, autocommit=True):
        self.cursor = sqlite3.connect(cf.database)
        self.autocommit = autocommit
        self.table = 'metrics'

    def __enter__(self):
        return self
        
    def __exit__(self, type_, value, traceback):
        self.cursor.close()

    def execute(self, sql):
        self.cursor.execute(sql)
        if self.autocommit:
            self.cursor.commit()

    def fetchall(self, sql):
        return self.cursor.execute(sql)

    def insert_metric(self, ip, metric_key, metric_value):
        sql = """
INSERT INTO `{}` (ip, metric_key, metric_value, ts)
VALUES ('{}', '{}', {}, {})
        """.format(self.table, ip, metric_key, metric_value, int(time.time()))
        self.execute(sql)


# Database singleton
db = DB()


# Install database schema
try:
    db.execute('''
CREATE TABLE `{}` (
    ip VARCHAR(16),
    metric_key VARCHAR(16),
    metric_value VARCHAR(16),
    ts INT)
'''.format(db.table))

    db.execute('''
CREATE INDEX ip_index on (ip)
''')
except sqlite3.OperationalError:
    pass
