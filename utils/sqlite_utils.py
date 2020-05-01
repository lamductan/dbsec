import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file, isolation_level=None)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(c, create_table_sql):
    """ create a table from the create_table_sql statement
    :param c: Cursor object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_index(c, create_index_sql):
    """ create an index for the table from the create_index_sql statement
    :param c: Cursor object
    :param create_index_sql: a CREATE [UNIQUE] INDEX statement
    :return:
    """
    try:
        c.execute(create_index_sql)
    except Error as e:
        print(e)
