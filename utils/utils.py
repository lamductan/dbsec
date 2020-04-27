import os
import json
import pickle
import re


def make_dirs(dirname):
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

def load_json(filepath):
    try:
        with open(filepath, "r") as read_file:
            data = json.load(read_file)
            return data
    except:
        raise Exception("Cannot load config file")

def save_json(data, filepath):
    try:
        dirname = os.path.dirname(filepath)
        make_dirs(dirname)
        with open(filepath, "w") as write_file:
            json.dump(data, write_file)
    except:
        raise Exception("Cannot write config file")

# Data
def cache_data(data, path):
    dir_prefix = os.path.dirname(path)
    make_dirs(dir_prefix)
    with open(path, 'wb') as f:
        pickle.dump(data, f)

def restore_data(path):
    with open(path, 'rb') as f:
        data = pickle.load(f)
        return data


def get_chunk_file_name(part_num):
    return 'part%04d' % part_num


def delete_chunk_files(chunk_dir):
    """
    Delete all the chunk files (any file matching the regex) from this provided directory.
    :param chunk_dir: directory whose chunk files are being deleted
    :return:
    """
    file_list = os.listdir(chunk_dir)
    for f in file_list:
        if re.fullmatch(r'^part[0-9][0-9][0-9][0-9]$', f):
            os.remove(os.path.join(chunk_dir, f))


def split_file(file_path, out_dir, chunk_size=1000000):
    """
    Split a file into chunks of a specific size, save these chunks
    to the provided directory, deleting all chunks already stored in
    the directory.
    :param file_path: path of file to be split
    :param out_dir: directory to save file chunks
    :param chunk_size: size of file chunks in bytes
    :return:
    """
    if not os.path.exists(file_path):
        raise Exception("file_path does not exist")
    if not os.path.isfile(file_path):
        raise Exception("file_path must be a file")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    if not os.path.isdir(out_dir):
        raise Exception("out_dir must be a directory")

    delete_chunk_files(out_dir)

    with open(file_path, "rb") as f:
        part_num = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            filename = os.path.join(out_dir, get_chunk_file_name(part_num))
            with open(filename, 'wb') as p:
                p.write(chunk)
            part_num = part_num + 1


def join_chunks(chunk_dir, out_file_path):
    """
    Join chunks of split file back together to recreate file
    :param chunk_dir: directory containing chunks of file
    :param out_file_path: path of file being created
    :return:
    """
    if not os.path.exists(chunk_dir):
        raise Exception("chunk_dir does not exist")
    if not os.path.isdir(chunk_dir):
        raise Exception("chunk_dir must be a directory")

    if not os.path.exists(os.path.dirname(out_file_path)):
        os.makedirs(os.path.dirname(out_file_path))

    with open(out_file_path, "wb") as output:
        part_num = 0
        while True:
            filename = os.path.join(chunk_dir, get_chunk_file_name(part_num))
            if not os.path.exists(filename):
                break
            with open(filename, "rb") as f:
                chunk = f.read()
                output.write(chunk)
            part_num = part_num + 1

