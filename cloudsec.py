import os
import sys
import time

from user import User

class BackupProgram():
    
    def __init__(self, user):
        self._user = user
        self._time_interval = 0
        print(self._user.get_list_bucket())

    def already_set_backup_folder_and_bucket(self):
        return True

    def set_backup_folder_and_bucket(self):
        return None

    def already_set_time_interval(self):
        return True

    def set_time_interval(self):
        return None

    def get_time_interval(self):
        return self._time_interval
    
    def is_backup_folder_modified(self):
        return False

    def upload_new_version(self):
        return None


def main():
    user = User("~/.aws/credentials")
    backupProgram = BackupProgram(user)
    if not backupProgram.already_set_backup_folder_and_bucket():
        backupProgram.set_backup_folder_and_bucket()
    if not backupProgram.already_set_time_interval():
        backupProgram.set_time_interval()

    while True:
        time.sleep(backupProgram.get_time_interval())
        if backupProgram.is_backup_folder_modified():
            backupProgram.upload_new_version()
        print("program ends")
        break


if __name__ == '__main__':
    main()
