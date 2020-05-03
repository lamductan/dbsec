from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import base64

def sha256(data):
    """
    Method to provide consistent hashing functionality using SHA256
    :param data: data to be hashed; can be a list
    :return: hash of data
    """
    my_sha256 = hashes.Hash(hashes.SHA256(), backend=default_backend())
    if isinstance(data, list):
        for d in data:
            try:
                my_sha256.update(bytes(str(d), "utf-8"))
            except (TypeError):
                print("invalid type")
    else:
        my_sha256.update(bytes(str(data), "utf-8"))
    return my_sha256.finalize()

def setPassword(plaintext, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(plaintext))

def symKey(key):
    return Fernet(key)

def genSymKey():
    return Fernet.generate_key()

def encryptFile(path):
    pass

def decryptFile(path):
    pass