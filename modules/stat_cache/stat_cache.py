import os
import sys
import shutil

from utils.utils import make_dirs, cache_data, restore_data 


class StatCache(object):
    
    def __init__(self, stat_cache_dir, backup_folder):
        self._stat_cache_dir = stat_cache_dir
        self._backup_folder = backup_folder

        self._latest_stat_cache_dir = os.path.join(stat_cache_dir, "latest")
        self._latest_stat_of_folder = os.path.join(
                self._latest_stat_cache_dir, "stat.dat")
        self._latest_stat_of_whole_folder = os.path.join(
                self._latest_stat_cache_dir, "backup")
        make_dirs(self._latest_stat_of_whole_folder)

        self._new_stat_cache_dir = os.path.join(stat_cache_dir, "new")
        self._new_stat_of_folder = os.path.join(
                self._new_stat_cache_dir, "stat.dat")
        self._new_stat_of_whole_folder = os.path.join(
                self._new_stat_cache_dir, "backup")
        make_dirs(self._new_stat_of_whole_folder)

    def is_backup_folder_modified(self):
        if not os.path.isfile(self._latest_stat_of_folder):
            stat_result = os.stat(self._backup_folder)
            cache_data(stat_result, self._latest_stat_of_folder)
            for f in os.scandir(self._backup_folder):
                if f.is_dir():
                    cache_data(os.stat(f), self._new_stat_of_whole_folder)
            return False
        else:
            new_stat_result = os.stat(self._backup_folder)
            old_stat_result = restore_data(self._latest_stat_of_folder)
            if new_stat_result.st_ctime == old_stat_result.st_ctime:
                return False
            else:
                cache_data(new_stat_result, self._new_stat_of_folder)
                for f in os.scandir(self._backup_folder):
                    if f.is_dir():
                        cache_data(os.stat(f), self._new_stat_of_whole_folder)
                return True

    def update_new_cache(self):
        shutil.rmtree(self._latest_stat_cache_dir)
        shutil.move(self._new_stat_cache_dir, self._latest_stat_cache_dir)
