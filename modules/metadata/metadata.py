import os

from utils.utils import split_file

class Metadata(object):
    def __init__(self):
        self.metadata = {}

    def update_metadata(self, path):
        # Set or update version number
        metadata = self.metadata[os.path.basename(path)]
        if not metadata:
            metadata["version"] = 1
        else:
            metadata["version"] += 1

        curr_metadata = metadata[metadata["version"]]
        prev_metadata = metadata[metadata["version"] - 1]

        out_dir = os.path.join(os.path.join(os.path.dirname(path), os.path.basename(path)),
                               self.metadata[path]["version"])
        split_file(path, out_dir)
        index = 0
        for file in os.listdir(out_dir):
            prev = False
            if metadata["version"] > 1:
                if index in curr_metadata["previous"]:
                    prev_out_dir = os.path.join(os.path.join(os.path.dirname(path), os.path.basename(path)),
                                                prev_metadata["previous"][index])
                else:
                    prev_out_dir = os.path.join(os.path.join(os.path.dirname(path), os.path.basename(path)),
                                                self.metadata[path]["version"] - 1)

                if self.chunks_equal(prev_out_dir, out_dir, file):
                    prev = True
            if prev:
                if index in prev_metadata["previous"]:
                    curr_metadata["previous"][index] = prev_metadata["previous"][index]
                else:
                    curr_metadata["previous"][index] = metadata["version"] - 1
            else:
                curr_metadata["new"] += index

        return 0

    def chunks_equal(self, prev_out_dir, out_dir, file, chunk_size=1000000):
        with open(os.path.join(prev_out_dir, file), "rb") as f1:
            with open(os.path.join(out_dir, file), "rb") as f2:
                prev_chunk = f1.read(chunk_size)
                curr_chunk = f2.read(chunk_size)
        return prev_chunk == curr_chunk
