import os
import sys
import threading

class ProgressPercentage(object):

    def __init__(self):
        self.seen_so_far = 0
        self.lock = threading.Lock()
        self.size = None
        self.filename = None

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self.lock:
            self.seen_so_far += bytes_amount
            percentage = (self.seen_so_far / self.size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self.filename, self.seen_so_far, self.size,
                    percentage))
            sys.stdout.flush()


class ProgressPercentageUpload(ProgressPercentage):
    
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.size = float(os.path.getsize(filename))


class ProgressPercentageDownload(ProgressPercentage):
    
    def __init__(self, client, bucket, filename, object_name):
        super().__init__()
        self.filename = filename
        self.size = client.head_object(
                Bucket=bucket, Key=object_name)["ContentLength"]

