import getpass
import os
import shutil
import signal
import time

from modules.metadata.metadata import Metadata
from modules.object_db.object_db import ObjectDB
from modules.stat_cache.stat_cache import StatCache
from utils.crypto import sha256, setPassword, symKey, genSymKey, encryptFile, decryptFile
from utils.utils import make_dirs, load_json, save_json
from utils.utils import recursive_get_hash_list, get_hash_list_file_objects
from utils.utils import replace_backslashes_with_forward_slashes

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
        :return: string, the path of new metadata
        """
        for file_object_path in new_file_object_paths:
            object_name = os.path.relpath(file_object_path, self._PREFIX_PATH)
            object_name = replace_backslashes_with_forward_slashes(object_name)
            self._user.upload_file(file_object_path, self._bucket, object_name)
        
        new_metadata_dir = os.path.join(
                self._metadata_dir, "v{}".format(self._version))
        make_dirs(new_metadata_dir)
        self.upload_new_metadata(new_metadata_dir)
        return new_metadata_dir


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
        return path


    def _copy_old_metadata_and_get_set_file_ids_if_unmodified(self, list_unmodified_files):
        """
        Copy metadata of old version to current version
        :param list_unmodified_files: list of strings, each string is
            a path of an unmodified file
        :return: set of integers, containing file ids of unmodified files
        """
        set_file_ids = set()
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
            if os.path.isfile(old_version_path):
                # file already exists
                shutil.copy(old_version_path, new_version_path)
                file_ids = Metadata.read(new_version_path).file_ids
                for file_id in file_ids:
                    set_file_ids.add(file_id)
            else:
                # deal with duplicated file: create new metadata for them
                chunk_paths_and_hashes = \
                        self._object_db.get_chunk_paths_and_hashes(filepath)
                file_ids = []
                data_keys = []
                for chunk_path, h in chunk_paths_and_hashes.items():
                    file_id, data_key = self._object_db.query(h)
                    file_ids.append(file_id)
                    data_keys.append(data_key)
                self._create_new_metadata_of_modified_file(
                    filepath, file_ids, data_keys)

        return set_file_ids

    def flush_version_to_file(self):
        with open(self._VERSION_FILEPATH, "w") as f:
            f.write(str(self._version))


    def interrupt(self, signum, frame):
        print('TIMED OUT!')
        raise TimeoutError

    def version_prompt(self):
        try:
            prompt = "Enter a version number"
            if self._version > 1:
                prompt += "(1-{})".format(self._version)
            prompt += ": "
            # NOTE: for testing
            version = int(input(prompt).strip())
            return version
        except TypeError as te:
            print("Invalid integer!")
            return
        except:
            print("Timeout!")
            return

    def backup_dir_prompt(self):
        try:
            prompt = "Enter a directory to save your backup: "
            # NOTE: for test
            backup_dir = "../test"
            #backup_dir = str(input(prompt).strip())
            backup_dir = os.path.abspath(backup_dir)
            try:
                print("your backup_dir: ", backup_dir)
                make_dirs(backup_dir)
            except:
                print("Invalid directory!")
                return
            return backup_dir
        except:
            print("Timeout!")
            return

    def _get_file_object_ids_from_metadata(self, metadata_dir):
        set_file_object_ids = set()
        for f in os.listdir(metadata_dir):
            f = os.path.join(metadata_dir, f)
            if os.path.isfile(f):
                metadata = Metadata.read(f)
                file_ids = metadata.file_ids
                for file_id in file_ids:
                    set_file_object_ids.add(file_id)
            else:
                set_file_object_ids_in_f = self._get_file_object_ids_from_metadata(f)
                for file_id in set_file_object_ids_in_f:
                    set_file_object_ids.add(file_id)
        return set_file_object_ids


    def _retrieve_backup_data_from_file_objects_and_metadata(self,
            encrypted_file_objects_dir, metadata_dir, backup_data_dir,
            original_metadata_dir):
        """
        Decrypt data keys by control key, then decrypt file objects by data
        key and join these file objects
        :param encrypted_file_objects_dir: string, path of directory containing
            encrypted file objects downloaded from S3
        :param metadata_dir: string, path of metadata_dir
        :param backup_data_dir: string, path of folder containing retrieved backup
            data
        :param original_metadata_dir: metadata dir in the first call
            (not recursive)
        :return
        """
        for metadata_path in os.listdir(metadata_dir):
            metadata_path = os.path.join(metadata_dir, metadata_path)
            if os.path.isfile(metadata_path):
                backup_file_path_rel = os.path.relpath(
                        metadata_path, original_metadata_dir)
                backup_file_path_rel = backup_file_path_rel[
                        :backup_file_path_rel.find(".metadata")]
                metadata = Metadata.read(metadata_path)
                data_keys = self.decrypt_data_keys(metadata.encrypted_data_keys)
                backup_file_path = os.path.join(
                        backup_data_dir, backup_file_path_rel)
                make_dirs(os.path.dirname(backup_file_path))
                with open(backup_file_path, "wb") as f:
                    for file_id, data_key in \
                            zip(metadata.file_ids, data_keys):
                        encrypted_file_object_path = os.path.join(
                                encrypted_file_objects_dir, str(file_id))
                        chunk = decryptFile(data_key, encrypted_file_object_path)
                        f.write(chunk)
            else:
                self._retrieve_backup_data_from_file_objects_and_metadata(
                    encrypted_file_objects_dir, metadata_path, backup_data_dir,
                    original_metadata_dir)

    def retrieve_backup(self):
        try:
            signal.alarm(10)
            print("Do you want to retrieve backup from a previous version (y/n)?", end=" ", flush=True)
            response = input().strip()
            signal.alarm(0)
            if response[0].lower() == 'n':
                return
            elif response[0].lower() != 'y':
                print("Invalid input.")
                return
            print("Retrieving backup")
            signal.alarm(5)
            retrieve_version = self.version_prompt()
            signal.alarm(0)
            if not retrieve_version:
                return
            signal.alarm(5)
            backup_dir = self.backup_dir_prompt()
            signal.alarm(0)
            if not backup_dir:
                return
            print("Retrieved backup")
        except TimeoutError:
            return
        except Exception as e:
            print(f"Error: {e}")

        # Download metadata
        backup_dir = os.path.join(backup_dir, "v{}".format(retrieve_version))
        metadata_dir = os.path.join(backup_dir, "metadata/v{}".format(retrieve_version))
        # NOTE: comment 2 lines below for test
        self._user.download_folder(self._bucket,
                "metadata/v{}".format(retrieve_version), backup_dir)

        # Download encrypted file objects
        encrypted_file_objects_dir = os.path.join(backup_dir, ".tmp")
        make_dirs(encrypted_file_objects_dir)
        set_file_object_ids = self._get_file_object_ids_from_metadata(metadata_dir)
        print(set_file_object_ids)
        # NOTE: comment 4 lines below for test
        for file_id in set_file_object_ids:
            object_name = "file_objects/{}".format(file_id)
            file_name = os.path.join(encrypted_file_objects_dir, str(file_id))
            self._user.download_file(file_name, self._bucket, object_name)

        # Compute hash of downloaded files and compare with hash of this version on eth
        hashes_of_file_objects = get_hash_list_file_objects(
                encrypted_file_objects_dir, set_file_object_ids)
        hashes_of_metadata = recursive_get_hash_list(metadata_dir)
        hashList = hashes_of_file_objects + hashes_of_metadata
        allHashes = sha256(hashList).hex()
        print("all hashes of retrieve backup: ", allHashes)
        # Get id of transaction corresponding to this version on eth
        version, txn_hash = self._object_db.queryHashVer(retrieve_version)
        assert int(version) == retrieve_version
        print("txn_hash = ", txn_hash)
        allHashesStoredOnEth = self._eth.retrieve(txn_hash)[2:] #remove 0x prefix
        print("hash store on eth:             ", allHashesStoredOnEth)
        if allHashes != allHashesStoredOnEth:
            print("Backup data on S3 bucket at version {} is modified!"
                    .format(retrieve_version))
        else:
            print("Retrieving your backup version...")
            backup_data_dir = os.path.join(backup_dir, "data")
            original_metadata_dir = metadata_dir
            self._retrieve_backup_data_from_file_objects_and_metadata(
                    encrypted_file_objects_dir, metadata_dir, backup_data_dir,
                    original_metadata_dir)
            print("Successfully retrieve your backup at version {}".format(
                retrieve_version))


    def run(self):
        """
        Method to run the backup program.
        """
        if not self.is_already_config():
            self.config()

        signal.signal(signal.SIGALRM, self.interrupt)
        while True:
            print("version: ", self._version)
            modified, list_modified_files, list_unmodified_files = \
                    self.is_backup_folder_modified()
            print("modified: ", modified)
            if modified:
                self._version += 1
                # update object_db and metadata of modified files
                new_file_object_paths = []
                set_file_object_ids = set()
                for filepath in list_modified_files:
                    print(filepath)
                    chunk_paths_and_hashes = \
                            self._object_db.get_chunk_paths_and_hashes(filepath)
                    file_ids = []
                    data_keys = []
                    for chunk_path, h in chunk_paths_and_hashes.items():
                        file_id, data_key = self._object_db.query(h)
                        if file_id is None:
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

                        file_ids.append(file_id)
                        data_keys.append(data_key)
                        set_file_object_ids.add(file_id)

                    self._create_new_metadata_of_modified_file(
                        filepath, file_ids, data_keys)

                # update metadata of unmodified files
                set_file_ids_of_unmodified_files = \
                        self._copy_old_metadata_and_get_set_file_ids_if_unmodified( \
                            list_unmodified_files)
                new_metadata_dir = self.upload_new_version(new_file_object_paths)
                print("new_metadata_dir = ", new_metadata_dir)
                self._stat_cache.update_new_cache()

                # Compute hash and upload to eth
                for file_id in set_file_ids_of_unmodified_files:
                    set_file_object_ids.add(file_id)
                hashes_of_file_objects = get_hash_list_file_objects(
                        self._file_objects_dir, set_file_object_ids)
                hashes_of_metadata = recursive_get_hash_list(new_metadata_dir)
                hashList = hashes_of_file_objects + hashes_of_metadata
                #hash all hashes, and upload to eth
                allHashes = sha256(hashList).hex()
                print("all hashes of new version: ", allHashes)
                transaction_id = self._eth.upload(allHashes)
                # save transaction and version
                self._object_db.insertHashVer(self._version, transaction_id)

                self.flush_version_to_file()
            else:
                self.retrieve_backup()
            time.sleep(self.get_time_interval())

    def __del__(self):
        self.flush_version_to_file()
        print("program ends")
