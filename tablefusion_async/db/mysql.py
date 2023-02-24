import MySQLdb
import MySQLdb.cursors
from contextlib import contextmanager


from tablefusion_async import config

POOL = {}

Cursor = MySQLdb.cursors.Cursor
DictCursor = MySQLdb.cursors.DictCursor
SSCursor = MySQLdb.cursors.SSCursor
SSDictCursor = MySQLdb.cursors.SSDictCursor


@contextmanager
def get_conn_cursor(db, cursor_type=Cursor):
    connection = MySQLdb.connect(
        host=config.MYSQL_INFO[db]['host'],
        user=config.MYSQL_INFO[db]['username'],
        password=config.MYSQL_INFO[db]['password'],
        db=config.MYSQL_INFO[db]['db'],
        charset=config.MYSQL_INFO[db]['charset'],
        port=config.MYSQL_INFO[db]['port'],
        cursorclass=cursor_type
    )
    cursor = connection.cursor()
    try:
        yield connection, cursor
    finally:
        cursor.close()
        connection.close()


def mysql_select(sql, *params, db='dde_deepdive', cursor_type=Cursor):
    with get_conn_cursor(db, cursor_type) as (connection, cursor):
        cursor.execute(sql, params)
        results = cursor.fetchall()
    return results


def mysql_execute(sql, *params, db='dde_deepdive') -> int:  # 返回last row id
    with get_conn_cursor(db) as (connection, cursor):
        try:
            cursor.execute(sql, params)
            connection.commit()
            return cursor.lastrowid
        except Exception as e:
            connection.rollback()
            raise e


def mysql_executemany(sql, params_list, db='dde_deepdive') -> int:  # 返回last row id
    with get_conn_cursor(db) as (connection, cursor):
        try:
            cursor.executemany(sql, params_list)
            connection.commit()
            return cursor.lastrowid
        except Exception as e:
            connection.rollback()
            raise e
