import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


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
    """
    Method to easily generate a password, using SHA256
    :param plaintext: plaintext password
    :param salt: salt to use
    :return: hashed and salted password
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(plaintext))

def symKey(key):
    """
    Simple alias to Fernet module
    :param key: key to use
    :return: Fernet module using key
    """
    return Fernet(key)

def genSymKey():
    """
    Simple alias to generate a symmetric key
    :return: symmetric key
    """
    return Fernet.generate_key()

def encryptFile(key, input_path, output_path):
    """
    Encrypt a file, and write out using a symmetric key
    :param key: key to use
    :param input_path: input file to encrypt
    :param output_path: output file
    """
    fernet = symKey(key)
    with open(input_path, "rb") as f:
        encrypted = fernet.encrypt(f.read())
    with open(output_path, "wb") as f:
        f.write(encrypted)

def decryptFile(key, input_path, output_path=None):
    """
    Decrypt a file, and optionally write out
    :param key: key to use
    :param input_path: input file to decrypt
    :param output_path: output file
    :return: decrypted data
    """
    fernet = symKey(key)
    with open(input_path, "rb") as f:
        decrypted = fernet.decrypt(f.read())
    if output_path != None:
        with open(output_path, "wb") as f:
            f.write(decrypted)
    return decrypted
