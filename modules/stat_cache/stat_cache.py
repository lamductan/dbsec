import os
import shutil

from modules.metadata.metadata import Metadata
from utils.utils import make_dirs, cache_data, restore_data

class StatCache(object):

	def __init__(self, stat_cache_dir, backup_folder):
		self._stat_cache_dir = stat_cache_dir  # str, abs path
		self._backup_folder = backup_folder  # str, abs path

		# latest file backup
		self._latest_stat_cache_dir = os.path.join(stat_cache_dir, "latest")
		make_dirs(self._latest_stat_cache_dir)

		# newest file backup; compared to latest
		self._new_stat_cache_dir = os.path.join(stat_cache_dir, "new")
		make_dirs(self._new_stat_cache_dir)

		# root stat file
		self._root_stat = os.path.join(self._latest_stat_cache_dir,
			os.path.basename(self._backup_folder) + ".dir")

		self.initialized = True


	def getLocalPath(self, path):
		# return str(path.path).replace(self._backup_folder, "")[1:]	#drop the leading slash
		common = os.path.commonpath([path, self._backup_folder])
		localPath = str(os.path.abspath(path)).replace(common, "")[1:]	#drop the leading slash
		if localPath == "":
			return os.path.basename(self._backup_folder)
		return os.path.join(os.path.basename(self._backup_folder), localPath)

	def getSuffix(self, path):
		#directory stat files have the following name: <directory_name>.dir
		#file stat files have the following name: <file_name>.file
		if os.path.isdir(path):	#is a dir
			suffix = ".dir"
		else:				#is a file
			suffix = ".file"
		return suffix

	def _recursive_file_check(self, path, list_modified_files, list_unmodified_files):
		modified = False

		localPath = self.getLocalPath(path)
		suffix = self.getSuffix(path)

		newStatPath = os.path.join(self._new_stat_cache_dir, localPath + suffix)
		latestStatPath = os.path.join(self._latest_stat_cache_dir, localPath + suffix)

		# print(os.path.basename(latestStatPath))

		if not os.path.isfile(latestStatPath):
			#stat file does not exist for path, so it must be new
			# print("DNE")
			modified = True
		#stat and write
		statResult = os.stat(path)
		cache_data(statResult, newStatPath)
		#compare to existing stat file, if it exists (not modified yet)
		if not modified:
			latestStatResult = restore_data(latestStatPath)
			if statResult.st_ctime != latestStatResult.st_ctime \
					or statResult.st_mtime != latestStatResult.st_mtime:
				# print("DIFF TIME")
				# print(statResult.st_ctime)
				# print(latestStatResult)
				modified = True

		if os.path.isfile(path):
			if modified:
				list_modified_files.append(path)
			else:
				list_unmodified_files.append(path)

		else: # if this is a directory, recursively check
			for f in os.scandir(path):
				file_updated = self._recursive_file_check(
						f.path, list_modified_files,
						list_unmodified_files)
				if file_updated:
					modified = True

		return modified


	def recursive_file_check(self, path):
		list_modified_files = []
		list_unmodified_files = []
		modified = self._recursive_file_check(
				path, list_modified_files, list_unmodified_files)
		return modified, list_modified_files, list_unmodified_files

	def is_backup_folder_modified(self):
		modified = False
		list_modified_files = None
		list_unmodified_files = None
		if not os.path.isfile(self._root_stat):  # first time executing
			modified = True  # should this be modified? data might not be in cloud yet
			# self.initialized = False
			_, list_modified_files, list_unmodified_files = \
					self.recursive_file_check(self._backup_folder)
		else:
			# self.initialized = True
			modified, list_modified_files, list_unmodified_files = \
					self.recursive_file_check(self._backup_folder)
		return modified, list_modified_files, list_unmodified_files


	def set_metadata(self, data):
		# TODO: load the metadata pulled from blockchain into here
		pass

	def update_new_cache(self):
		if self.initialized:  # we only want to update the latest with the new cache if new cache is present
			shutil.rmtree(self._latest_stat_cache_dir)
			shutil.move(self._new_stat_cache_dir, self._latest_stat_cache_dir)
