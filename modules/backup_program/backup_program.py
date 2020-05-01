import os
import time
import shutil

from modules.user.user import User
from modules.metadata.metadata import Metadata
from modules.object_db.object_db import ObjectDB
from modules.stat_cache.stat_cache import StatCache
from utils.utils import make_dirs, load_json, save_json, restore_data


HOME_DIRECTORY = os.path.expanduser("~")


class BackupProgram(object):
    
    def __init__(self, user):
        self._PREFIX_PATH = os.path.join(HOME_DIRECTORY, ".aws/.backup_program/")
        self._CONFIG_FILEPATH = os.path.join(self._PREFIX_PATH, "config.json")
        self._VERSION_FILEPATH = os.path.join(self._PREFIX_PATH, "__version__.txt")
        self._user = user
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


    def is_already_config(self):
        if not os.path.isfile(self._CONFIG_FILEPATH):
            return False
        config = load_json(self._CONFIG_FILEPATH)
        config_keys = config.keys()
        if not "backup_folder" in config_keys \
                or not "bucket" in config_keys \
                or not "time_interval" in config_keys:
            return False
        print("Backup program is already config")
        self._backup_folder = config["backup_folder"]
        self._bucket = config["bucket"]
        self._time_interval = config["time_interval"]
        self._stat_cache = StatCache(self._stat_cache_dir, self._backup_folder)
        self._object_db = ObjectDB(self._object_db_path)
        return True


    def config(self):
        self._set_backup_folder()
        self._set_bucket()
        self._set_time_interval()
        self._stat_cache = StatCache(self._stat_cache_dir, self._backup_folder)
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
        return: boolean, True if backup folder was modified, False otherwise.
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
            self._user.upload_file(file_object_path, self._bucket, object_name)
        
        new_metadata_dir = os.path.join(
                self._metadata_dir, "v{}".format(self._version))
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
                self._user.upload_file(metadata_path, self._bucket, object_name)
            else:
                self.upload_new_metadata(metadata_path)


    def _create_new_metadata_of_modified_file(
            self, filepath, file_ids, data_keys, control_key=None):
        """
        Create new metadata of a modified file
        :param filepath: path of modified file
        :param file_ids: list integer, ids of file objects 
            which are chunks of this file
        :param data_keys: list string, keys to encrypt/decrypt file objects
        :param control_key: string, key to encrypt data_keys
        :return
        """
        encrypted_data_keys = data_keys
        #TODO: encrypted_data_keys = encrypt(data_keys, control_key)
        relative_path_from_backup_root = os.path.relpath(
                filepath, self._backup_folder)
        metadata = Metadata(relative_path_from_backup_root, file_ids, 
                encrypted_data_keys, self._version)
        path = os.path.join(self._metadata_dir, "v{}".format(self._version),
                relative_path_from_backup_root + ".metadata")
        make_dirs(os.path.dirname(path))
        metadata.save(path)
        return path


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
                for filepath in list_modified_files:
                    print(filepath)
                    chunk_paths_and_hashes = \
                            self._object_db.get_chunk_paths_and_hashes(filepath)
                    file_ids = []
                    data_keys = []
                    for chunk_path, h in chunk_paths_and_hashes.items():
                        file_id_and_data_key = self._object_db.query(h)
                        file_id = None
                        data_key = None
                        if file_id_and_data_key is None:
                            data_key = ""
                            #TODO: generate new data key for new chunk file
                            file_id = self._object_db.insert(h, data_key)
                            file_id, data_key = (file_id, data_key)
                            file_object_path = os.path.join(self._file_objects_dir,
                                    str(file_id))
                            shutil.move(chunk_path, file_object_path)
                            new_file_object_paths.append(file_object_path)
                        else:
                            file_id, data_key = file_id_and_data_key
                        file_ids.append(file_id)
                        data_keys.append(data_key)

                    new_metadata = self._create_new_metadata_of_modified_file(
                        filepath, file_ids, data_keys, control_key=None)
                    # For testing only
                    # metadata = restore_data(new_metadata)
                    # print(metadata.file_ids)
                    # print(metadata.encrypted_data_keys)

                # update metadata of unmodified files
                self._copy_old_metadata_if_unmodified(list_unmodified_files)
                self.upload_new_version(new_file_object_paths)
                self._stat_cache.update_new_cache()
                
            time.sleep(self.get_time_interval())


    def __del__(self):
        with open(self._VERSION_FILEPATH, "w") as f:
            f.write(str(self._version))
        print("program ends")
