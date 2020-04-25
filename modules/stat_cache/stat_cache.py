import os
import sys
import shutil

from utils.utils import make_dirs, cache_data, restore_data 


class StatCache(object):
	
	def __init__(self, stat_cache_dir, backup_folder):
		self._stat_cache_dir = stat_cache_dir
		self._backup_folder = backup_folder

		#latest folder will hold the stat.dat, which contains the latest info for the root target directory
		#latest/backup folder will hold the latest info for each file, and will also follow the target directory structure
		self._latest_stat_cache_dir = os.path.join(stat_cache_dir, "latest")
		self._latest_stat_of_folder = os.path.join(
				self._latest_stat_cache_dir, "stat.dat")
		self._latest_stat_of_whole_folder = os.path.join(
				self._latest_stat_cache_dir, "backup")
		make_dirs(self._latest_stat_of_whole_folder)

		#similar backup pattern for the new folder
		self._new_stat_cache_dir = os.path.join(stat_cache_dir, "new")
		self._new_stat_of_folder = os.path.join(
				self._new_stat_cache_dir, "stat.dat")
		self._new_stat_of_whole_folder = os.path.join(
				self._new_stat_cache_dir, "backup")
		make_dirs(self._new_stat_of_whole_folder)

		self.initialized = True

		self.metadata = {
			"previous": {},
			"key": "",
			"new": {}
		}

	def recursive_file_check(self, path):
		modified = False
		localPath = str(path.path).replace(self._backup_folder, "")[1:]	#drop the leading slash
		print(localPath)
		if path.is_dir():
			print("directory")
			for f in os.scandir(path):
				file_updated = self.recursive_file_check(f)
				if not modified and file_updated:
					modified = True
		else:
			print("file")
		return modified

	def is_backup_folder_modified(self):
		modified = False
		if not os.path.isfile(self._latest_stat_of_folder):     #stat.dat does not exist; first time executing program
			modified = True
			self.initialized = False
			stat_result = os.stat(self._backup_folder)
			cache_data(stat_result, self._latest_stat_of_folder)
			#TODO: update the metadata using the root folder and recursively scanning the root
			for f in os.scandir(self._backup_folder):
				# print(f)
				self.recursive_file_check(f)
				# if f.is_dir():
				#     cache_data(os.stat(f), self._new_stat_of_whole_folder)
		else:
			self.initialized = True
			new_stat_result = os.stat(self._backup_folder)
			old_stat_result = restore_data(self._latest_stat_of_folder)

			#check if root folder is modified
			if new_stat_result.st_ctime != old_stat_result.st_ctime:
				cache_data(new_stat_result, self._new_stat_of_folder)	#overwrite the latest version
				modified = True
			#TODO: update the metadata using the root folder and recursively scanning the root
			for f in os.scandir(self._backup_folder):
				# print(f)
				file_updated = self.recursive_file_check(f)
				if not modified and file_updated:
					modified = True
			# if new_stat_result.st_ctime == old_stat_result.st_ctime:
			# 	#root folder was not modified, but need to check individual files
			# 	for f in os.scandir(self._backup_folder):
			# 		recursive_file_check(f)
			# else:
			# 	cache_data(new_stat_result, self._latest_stat_of_folder)	#overwrite the latest version
			# 	for f in os.scandir(self._backup_folder):
			# 		print(f)
			# 		# if f.is_dir():
			# 		#     cache_data(os.stat(f), self._new_stat_of_whole_folder)
			# 	return True
		print()
		return modified

	def set_metadata(self, data):
		# TODO: load the metadata pulled from blockchain into here
		pass

	def update_new_cache(self):
		if self.initialized:	#we only want to update the latest with the new cache if new cache is present
			print("moving")
			shutil.rmtree(self._latest_stat_cache_dir)
			shutil.move(self._new_stat_cache_dir, self._latest_stat_cache_dir)
