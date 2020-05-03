import os
import time
import shutil
import getpass
import base64

from modules.user.user import User
from modules.metadata.metadata import Metadata
from modules.object_db.object_db import ObjectDB
from modules.stat_cache.stat_cache import StatCache
from utils.utils import make_dirs, load_json, save_json, restore_data, replace_backslashes_with_forward_slashes
from utils.crypto import sha256, setPassword, symKey, genSymKey, encryptFile, decryptFile

HOME_DIRECTORY = os.path.expanduser("~")

class BackupProgram(object):
    
    def __init__(self, user, eth):
        self._PREFIX_PATH = os.path.join(HOME_DIRECTORY, ".aws", ".backup_program")
        self._CONFIG_FILEPATH = os.path.join(self._PREFIX_PATH, "config.json")
        self._VERSION_FILEPATH = os.path.join(self._PREFIX_PATH, "__version__.txt")

        self._user = user
        self._eth = eth
        self._backup_folder = None
        self._bucket = None
        self._time_interval = 10
        self._list_bucket_name = self._user.get_list_bucket_name()
        print("List bucket name of user: ", self._list_bucket_name)
        
        self._version = None
        if os.path.isfile(self._VERSION_FILEPATH):
            with open(self._VERSION_FILEPATH, "r") as f:
                self._version = int(f.readline())
        else:
            self._version = 0
        self._stat_cache_dir = os.path.join(self._PREFIX_PATH, "stat_cache")
        self._stat_cache = None
        self._object_db_path = os.path.join(self._PREFIX_PATH, "objects.db")
        self._object_db = None
        self._metadata_dir = os.path.join(self._PREFIX_PATH, "metadata")
        self._file_objects_dir = os.path.join(self._PREFIX_PATH, "file_objects")
        make_dirs(self._file_objects_dir)

        self._control_key_salt_dir = os.path.join(self._PREFIX_PATH, "salt_file")
        self._control_key = None
        self._salt = None

        self._password_test_file_dir = os.path.join(self._PREFIX_PATH, "password_test")
        self._password_test_message = b"This message will have been decrypted properly if you " \
                                      b"entered the correct password."


    def is_already_config(self):
        if not os.path.isfile(self._CONFIG_FILEPATH):
            return False
        config = load_json(self._CONFIG_FILEPATH)
        config_keys = config.keys()
        if not "backup_folder" in config_keys \
                or not "bucket" in config_keys \
                or not "time_interval" in config_keys:
            return False
        if not os.path.isfile(self._control_key_salt_dir):
            return False

        print("Backup program is already config")
        self._backup_folder = config["backup_folder"]
        self._bucket = config["bucket"]
        self._time_interval = config["time_interval"]
        self._stat_cache = StatCache(self._stat_cache_dir, self._backup_folder)
        self._object_db = ObjectDB(self._object_db_path)

        self._set_salt()
        while True:
            self._set_control_key()
            if self._correct_password_entered():
                break

        return True


    def config(self):
        self._set_backup_folder()
        self._set_bucket()
        self._set_time_interval()
        self._set_salt()
        self._set_control_key()
        self._create_password_test_file()
        self._stat_cache = StatCache(self._stat_cache_dir, self._backup_folder)
        self._object_db = ObjectDB(self._object_db_path)
        config = {
            "backup_folder": self._backup_folder,
            "bucket": self._bucket,
            "time_interval": self._time_interval,
        }
        save_json(config, self._CONFIG_FILEPATH)
        print(config)


    def _set_backup_folder(self):
        """
        Method to let user select the backup folder.
        Backup folder is a folder path input from keyboard.
        """
        print("1. Enter your backup folder:")
        backup_folder = None
        while True:
            print(">>> ", end="")
            backup_folder = str(input().strip())
            if not os.path.isdir(backup_folder): 
                print("Not found folder \"{}\". Please enter a valid path!"
                        .format(backup_folder))
            else:
                break
        self._backup_folder = os.path.abspath(backup_folder)


    def _set_bucket(self):
        """
        Method to let user select desired bucket.
        Bucket is a string input from keyboard.
        """
        print("2. Enter your selected bucket:")
        bucket = None
        while True:
            print(">>> ", end="")
            bucket = str(input().strip())
            if not bucket in self._list_bucket_name:
                print("Not found bucket {}. Please enter a valid bucket!"
                        .format(bucket))
            else:
                break
        self._bucket = bucket


    def _set_time_interval(self):
        """
        Method to set time interval.
        Time interval is an integer input from keyboard.
        """
        print("3. Enter your time interval to update backup:")
        time_interval = None
        while True:
            print(">>> ", end="")
            try:
                time_interval = int(input().strip())
                break
            except:
                print("Please input a valid integer number!")
        self._time_interval = time_interval

    def _set_salt(self):
        """
`       Set salt value by reading from file if file exists, or generating random value
        if file does not exist.
        """
        if os.path.isfile(self._control_key_salt_dir):
            with open(self._control_key_salt_dir, "rb") as f:
               self._salt = f.read()
        else:
            self._salt = os.urandom(16)
            with open(self._control_key_salt_dir, "wb") as f:
                f.write(self._salt)

    def _set_control_key(self):
        """
        Ask user to input password, use password and salt to generate control key
        """
        # NOTE: getpass doesn't seem to work with PyCharm's python console, but it works
        # in the terminal.
        password = getpass.getpass(prompt="Enter password: ").encode()
        self._control_key = setPassword(password, self._salt)

    def _create_password_test_file(self):
        """
        Create file with newly created control_key. Decrypting this file will be done to determine if
        correct password has been entered.
        """
        fernet = symKey(self._control_key)
        token = fernet.encrypt(self._password_test_message)
        with open(self._password_test_file_dir, "wb") as file:
            file.write(token)

    def _correct_password_entered(self):
        """
        Decrypt the password test file using the control key to see if the control key was derived using
        the correct password.
        :return: True if test file was decrypted correctly and password was entered correctly, False otherwise
        """
        fernet = symKey(self._control_key)
        with open(self._password_test_file_dir, "rb") as file:
            encrypted_message = file.read()
            try:
                decrypted_message = fernet.decrypt(encrypted_message)
                if decrypted_message == self._password_test_message:
                    return True
                else:
                    print("Incorrect Password")
                    return False
            except:
                print("Incorrect Password")
                return False

    def get_time_interval(self):
        """
        Method to get time interval.
        return: an integer indicating the selected time interval.
        """
        return self._time_interval
    

    def is_backup_folder_modified(self):
        """
        Check whether backup folder is modified with regard to
        the previous version.
        :return: boolean, True if backup folder was modified, False otherwise.
        """
        modified, list_modified_files, list_unmodified_files = \
                self._stat_cache.is_backup_folder_modified()
        if not modified:
            print("Backup folder is not modified.")
        else:
            print("Backup folder is modified. Upload new backup version")
        return modified, list_modified_files, list_unmodified_files


    def upload_new_version(self, new_file_object_paths):
        """
        Upload new version of backup if backup folder is modified.
        :param: new_file_object_paths: list of paths of new file_objects
        :return:
        """
        for file_object_path in new_file_object_paths:
            object_name = os.path.relpath(file_object_path, self._PREFIX_PATH)
            object_name = replace_backslashes_with_forward_slashes(object_name)
            self._user.upload_file(file_object_path, self._bucket, object_name)
        
        new_metadata_dir = os.path.join(
                self._metadata_dir, "v{}".format(self._version))
        make_dirs(new_metadata_dir)
        self.upload_new_metadata(new_metadata_dir)


    def upload_new_metadata(self, new_metadata_dir):
        """
        Upload new version of metadata.
        :param: new_metadata_dir: directory of new metadata
        :return:
        """
        for path in os.listdir(new_metadata_dir):
            metadata_path = os.path.join(new_metadata_dir, path)
            if os.path.isfile(metadata_path):
                object_name = os.path.relpath(metadata_path, self._PREFIX_PATH)
                object_name = replace_backslashes_with_forward_slashes(object_name)
                self._user.upload_file(metadata_path, self._bucket, object_name)
            else:
                self.upload_new_metadata(metadata_path)


    def encrypt_data_keys(self, data_keys):
        """
        Encrypt a list of data keys with the control key
        :param data_keys: list of data keys to be encrypted with the control key
        :return: list of encrypted data keys
        """
        f = symKey(self._control_key)
        encrypted_keys = []
        for key in data_keys:
            token = f.encrypt(key)
            encrypted_keys.append(token)
        return encrypted_keys

    def decrypt_data_keys(self, encrypted_data_keys):
        """
        Decrypt a list of encrypted data keys previously encrypted with the control key
        :param encrypted_data_keys: list of encrypted data keys to be decrypted with the control key
        :return: List of decrypted data keys
        """
        f = symKey(self._control_key)
        decrypted_keys = []
        for key in encrypted_data_keys:
            original_data_key = f.decrypt(key)
            decrypted_keys.append(original_data_key)
        return decrypted_keys

    def _create_new_metadata_of_modified_file(
            self, filepath, file_ids, data_keys):
        """
        Create new metadata of a modified file
        :param filepath: path of modified file
        :param file_ids: list integer, ids of file objects 
            which are chunks of this file
        :param data_keys: list string, keys to encrypt/decrypt file objects
        :return
        """

        encrypted_data_keys = self.encrypt_data_keys(data_keys)

        relative_path_from_backup_root = os.path.relpath(
                filepath, self._backup_folder)
        metadata = Metadata(relative_path_from_backup_root, file_ids, 
                encrypted_data_keys, self._version)
        path = os.path.join(self._metadata_dir, "v{}".format(self._version),
                relative_path_from_backup_root + ".metadata")
        make_dirs(os.path.dirname(path))
        metadata.save(path)
        return path, metadata.getHash()


    def _copy_old_metadata_if_unmodified(self, list_unmodified_files):
        """
        Copy metadata of old version to current version
        :param list_unmodified_files: list of strings, each string is
            a path of an unmodified file
        :return
        """
        for filepath in list_unmodified_files:
            relative_path_from_backup_root = os.path.relpath(
                    filepath, self._backup_folder)
            new_version_path = os.path.join(
                    self._metadata_dir, "v{}".format(self._version),
                    relative_path_from_backup_root + ".metadata")
            old_version_path = os.path.join(
                    self._metadata_dir, "v{}".format(self._version - 1),
                    relative_path_from_backup_root + ".metadata")
            make_dirs(os.path.dirname(new_version_path))
            shutil.copy(old_version_path, new_version_path)

    def flush_version_to_file(self):
        with open(self._VERSION_FILEPATH, "w") as f:
            f.write(str(self._version))

    def run(self):
        """
        Method to run the backup program.
        """
        if not self.is_already_config():
            self.config()
        
        while True:
            print("version: ", self._version)
            modified, list_modified_files, list_unmodified_files = self.is_backup_folder_modified()
            print("modified: ", modified)
            if modified:
                self._version += 1
                # update object_db and metadata of modified files
                new_file_object_paths = []
                hashList = []
                metadata_hashList = []
                for filepath in list_modified_files:
                    print(filepath)
                    chunk_paths_and_hashes = \
                            self._object_db.get_chunk_paths_and_hashes(filepath)
                    file_ids = []
                    data_keys = []
                    for chunk_path, h in chunk_paths_and_hashes.items():
                        hashList.append(h)
                        file_id_and_data_key = self._object_db.query(h)
                        file_id = None
                        data_key = None
                        if file_id_and_data_key is None:
                            data_key = genSymKey()
                            #save the key
                            file_id = self._object_db.insert(h, data_key)
                            file_object_path = os.path.join(self._file_objects_dir,
                                    str(file_id))
                            #encrypt the chunk, and write it to file_object_path
                            encryptFile(data_key, chunk_path, file_object_path)

                            #test decryption
                            # print(decryptFile(data_key, file_object_path, file_object_path))

                            new_file_object_paths.append(file_object_path)
                        else:
                            file_id, data_key = file_id_and_data_key
                        file_ids.append(file_id)
                        data_keys.append(data_key)

                    new_metadata, metadata_hash = self._create_new_metadata_of_modified_file(
                        filepath, file_ids, data_keys)
                    metadata_hashList.append(metadata_hash)
                    # For testing only
                    # metadata = restore_data(new_metadata)
                    # print(metadata.file_ids)
                    # print(metadata.encrypted_data_keys)
                hashList += metadata_hashList
                #hash all hashes, and upload to eth
                allHashes = sha256(hashList)
                print("all hashes:", allHashes)
                transaction_id = self._eth.upload(allHashes)
                #save transaction and version
                self._object_db.insertHashVer(self._version, transaction_id)
                #example to pull transaction id
                # print(self._object_db.queryHashVer(self._version))

                # update metadata of unmodified files
                self._copy_old_metadata_if_unmodified(list_unmodified_files)
                self.upload_new_version(new_file_object_paths)
                self._stat_cache.update_new_cache()
                self.flush_version_to_file()
            time.sleep(self.get_time_interval())


    def __del__(self):
        with open(self._VERSION_FILEPATH, "w") as f:
            f.write(str(self._version))
        print("program ends")
