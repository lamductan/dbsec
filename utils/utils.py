import os
import json
import pickle


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
