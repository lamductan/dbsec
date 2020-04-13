import os
import sys
import threading

class ProgressPercentage(object):

    def __init__(self):
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._size = None
        self._filename = None

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()


class ProgressPercentageUpload(ProgressPercentage):
    
    def __init__(self, filename):
        super.__init__(self)
        self._filename = filename
        self._size = float(os.path.getsize(filename))


class ProgressPercentageDownload(ProgressPercentage):
    
    def __init__(self, client, bucket, filename):
        super.__init(self)
        self._filename = filename
        self._size = client.head_object(Bucket=bucket, Key=filename).ContentLength

