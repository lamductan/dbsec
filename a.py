from modules.metadata.metadata import Metadata
from utils.utils import get_hash_list_file_objects
from utils.utils import recursive_get_hash_list
from utils.crypto import sha256

print("v1:")
metadata_v1 = Metadata.read("/home/tdlam/dev/phd/courseworks/data-security/projects/test/v1/metadata/v1/Genesis.txt.metadata")
print(metadata_v1.file_ids)
print("v2:")
metadata_v2 = Metadata.read("/home/tdlam/dev/phd/courseworks/data-security/projects/test/v2/metadata/v2/Genesis.txt.metadata")
print(metadata_v2.file_ids)

list_file_ids = [1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]

set_file_ids = set(list_file_ids)
print(set_file_ids)

hash_objects = get_hash_list_file_objects("/home/tdlam/dev/phd/courseworks/data-security/projects/test/v2/.tmp", set_file_ids)
hash_of_hash_objects = sha256(hash_objects).hex()
print("hash of objects   = ", hash_of_hash_objects)


hash_objects_1 = get_hash_list_file_objects("/home/tdlam/.aws/.backup_program/file_objects", set_file_ids)
hash_of_hash_objects_1 = sha256(hash_objects_1).hex()
print("hash of objects_1 = ", hash_of_hash_objects_1)

print()

hash_metadata = recursive_get_hash_list("/home/tdlam/dev/phd/courseworks/data-security/projects/test/v2/metadata/v2")
hash_of_hash_metadata = sha256(hash_metadata)
print("hash of metadata   = ", hash_of_hash_metadata)
hash_metadata_1 = recursive_get_hash_list("/home/tdlam/.aws/.backup_program/metadata/v2")
hash_of_hash_metadata_1 = sha256(hash_metadata_1)
print("hash of metadata_1 = ", hash_of_hash_metadata_1)

print()
all_hashes = hash_objects + hash_metadata
all_hashes = sha256(all_hashes).hex()
print("all hashes = ", all_hashes)
