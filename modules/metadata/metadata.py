import os
from utils.utils import cache_data

class Metadata(object):
    def __init__(self, filename, file_ids, encrypted_data_keys, version):
        self.filename = filename
        self.file_ids = file_ids
        self.encrypted_data_keys = encrypted_data_keys
        self.version = version
        
         
    def save(self, path):
        cache_data(self, path)
