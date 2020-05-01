import os
import shutil

from utils.utils import split_file_and_get_hash, make_dirs
from utils.sqlite_utils import create_connection, create_table, create_index


class ObjectDB(object):
    def __init__(self, object_db_path):
        self._object_db_path = object_db_path
        self._counter = 0
        self._conn = None
        self._c = None
        self._tmp_dir = os.path.join(os.path.dirname(self._object_db_path), ".tmp")
        make_dirs(self._tmp_dir)

        self._conn = create_connection(object_db_path)
        try:
            self._c = self._conn.cursor()
        except:
            print("Cannot create db connection!")

        sql_create_objects_table = """ CREATE TABLE IF NOT EXISTS objects (
                                           hash text NOT NULL,
                                           data_key text
                                    ); """     
        sql_create_index_on_hash = """ CREATE UNIQUE INDEX index_hash 
                                        ON objects(hash); """
        # create projects table
        create_table(self._c, sql_create_objects_table)
        # create tasks table
        create_index(self._c, sql_create_index_on_hash)


    def insert(self, hash_str, data_key=""):
        """ insert a row to table objects of db.
        :param hash_str: hash of a file
        :param data_key: data_key to encrypt
        :return: an integer indicating the last id of row.
        """
        try:
            self._c.execute("INSERT INTO objects values (?, ?)",
                            (hash_str, data_key))
            return self._c.lastrowid
        except Error as e:
            print(e)


    def query(self, hash_str):
        """ query a hash in the table.
        :param hash_str: hash of a file
        :return: a tuple (id, data_key), where:
            id: an integer indicating rowid of file,
            data_key: a string indicating data key to enc/dec file object.
        """
        result = list(self._c.execute("SELECT * FROM objects WHERE hash=?", 
                      (hash_str,)))
        if len(result) == 1:
            return result[0]


    def get_chunk_paths_and_hashes(self, filepath):
        """
        Compute the hashes of chunks of a file.
        :param filepath: path of file
        :return: dictionary, with key is path of chunk 
            and value is string of hash of this chunk.
        """
        shutil.rmtree(self._tmp_dir)
        make_dirs(self._tmp_dir)
        return split_file_and_get_hash(filepath, self._tmp_dir)

    
    def __del__(self):
        self._conn.close()
