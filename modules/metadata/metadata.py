import os

from utils.utils import split_file

class Metadata(object):
    def __init__(self):
        self.metadata = {}

    def update_metadata(self, path):
        # Set or update version number
        basename = str(os.path.basename(path))
        if basename not in self.metadata:
            self.metadata[basename] = {}
        metadata = self.metadata[basename]
        if not metadata:
            metadata["version"] = 1
            metadata[1] = {}
        else:
            metadata["version"] += 1
            metadata[metadata["version"]] = {}
            prev_metadata = metadata[metadata["version"] - 1]

        curr_metadata = metadata[metadata["version"]]
        curr_metadata["new"] = []
        curr_metadata["previous"] = []

        print(os.path.join(os.path.join(os.path.dirname(path), basename + "_chunks"),
                           ("v" + str(self.metadata[basename]["version"]))))

        if not os.path.exists(os.path.join(os.path.dirname(path), basename + "_chunks")):
            os.mkdir(os.path.join(os.path.dirname(path), basename + "_chunks"), )

        if not os.path.exists(os.path.join(os.path.join(os.path.dirname(path), basename + "_chunks"),
                                           ("v" + str(self.metadata[basename]["version"])))):
            os.mkdir(os.path.join(os.path.join(os.path.dirname(path), basename + "_chunks"),
                                  ("v" + str(self.metadata[basename]["version"]))))

        out_dir = str(os.path.join(os.path.join(os.path.dirname(path), basename + "_chunks"),
                                   str(self.metadata[basename]["version"])))
        print(os.path.join(os.path.dirname(os.path.abspath(__file__)), path))
        print(os.path.isfile(os.path.join(os.path.abspath(os.getcwd()), path)))
        split_file(os.path.join(os.path.abspath(os.getcwd()), path), out_dir)
        index = 0
        for file in os.listdir(out_dir):
            prev = False
            if metadata["version"] > 1:
                if index in curr_metadata["previous"]:
                    prev_out_dir = str(os.path.join(os.path.join(os.path.dirname(path), basename + "chunks"),
                                                    prev_metadata["previous"][index]))
                else:
                    prev_out_dir = str(os.path.join(os.path.join(os.path.dirname(path), basename + "chunks"),
                                                    self.metadata[basename]["version"] - 1))

                if self.chunks_equal(prev_out_dir, out_dir, file):
                    prev = True
            if prev:
                if index in prev_metadata["previous"]:
                    curr_metadata["previous"][index] = prev_metadata["previous"][index]
                else:
                    curr_metadata["previous"][index] = metadata["version"] - 1
            else:
                curr_metadata["new"] += [index]

        return 0

    def chunks_equal(self, prev_out_dir, out_dir, file, chunk_size=1000000):
        with open(os.path.join(prev_out_dir, file), "rb") as f1:
            with open(os.path.join(out_dir, file), "rb") as f2:
                prev_chunk = f1.read(chunk_size)
                curr_chunk = f2.read(chunk_size)
        return prev_chunk == curr_chunk
