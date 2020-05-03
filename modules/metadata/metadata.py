import os
from utils.utils import cache_data
from utils.crypto import sha256

class Metadata(object):
    def __init__(self, filename, file_ids, encrypted_data_keys, version):
        self.filename = filename
        self.file_ids = file_ids
        self.encrypted_data_keys = encrypted_data_keys
        self.version = version
        self.hash = self.computeHash()

    def computeHash(self):
    	return sha256([self.filename, self.file_ids, self.encrypted_data_keys, self.version])

    def getHash(self):
    	return self.hash
         
    def save(self, path):
        cache_data(self, path)
