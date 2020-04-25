import os
import sys
import time

from modules.user.user import User
from modules.stat_cache.stat_cache import StatCache
from utils.utils import load_json, save_json, restore_data


HOME_DIRECTORY = os.path.expanduser("~")


class BackupProgram(object):
    
    def __init__(self, user):
        self._CONFIG_FILEPATH = os.path.join(
                HOME_DIRECTORY, ".aws/.backup_program/config.json")
        self._user = user
        self._backup_folder = None
        self._bucket = None
        self._time_interval = 10
        self._list_bucket_name = self._user.get_list_bucket_name()
        print("List bucket name of user: ", self._list_bucket_name)
        self._stat_cache_dir = os.path.join(
                HOME_DIRECTORY, ".aws/.backup_program/stat_cache")

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
        return True

    def config(self):
        self._set_backup_folder()
        self._set_bucket()
        self._set_time_interval()
        self._stat_cache = StatCache(self._stat_cache_dir, self._backup_folder)
        config = {
            "backup_folder": self._backup_folder,
            "bucket": self._bucket,
            "time_interval": self._time_interval
        }
        save_json(config, self._CONFIG_FILEPATH)
        print(config)

    def _set_backup_folder(self):
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
        return self._time_interval
    
    def is_backup_folder_modified(self):
        if not self._stat_cache.is_backup_folder_modified():
            print("Backup folder is not modified.")
            return False
        else:
            print("Backup folder is modified. Upload new backup version")
            #generate and upload the new metadata
            #TODO: upload metadata and data
            return True

    def upload_new_version(self):
        self._stat_cache.update_new_cache()
        return None


def main():
    #setup AWS credentials
    user = User(os.path.join(HOME_DIRECTORY, ".aws/credentials"))
    #TODO: pull the metadata from the blockchain

    backupProgram = BackupProgram(user)

    if not backupProgram.is_already_config():
        backupProgram.config()

    loop = 0
    while True:
        if backupProgram.is_backup_folder_modified():
            backupProgram.upload_new_version()
        time.sleep(backupProgram.get_time_interval())
        # loop += 1
        # if loop == 5:
        #     break

    print("program ends")

if __name__ == '__main__':
    main()
