import os
import logging
import boto3
import io
from botocore.exceptions import ClientError

from utils.progress_percentage import ProgressPercentageUpload
from utils.progress_percentage import ProgressPercentageDownload

from utils.utils import get_chunk_file_name, make_dirs

class User(object):
    
    def __init__(self, aws_credential_path=os.path.join("~", ".aws", "credentials")):
        self._aws_credential_path = aws_credential_path
        self._client = boto3.client('s3')

    def get_list_bucket_name(self):
        reponse = self._client.list_buckets()
        return [bucket['Name'] for bucket in reponse['Buckets']]

    def upload_file_as_chunks(self, file_name, bucket, object_name=None, chunk_size=1000000):
        """
        Split a file into chunks and upload these chunks to an S3 bucket
        :param file_name: File to split and upload
        :param bucket: Bucket to upload to
        :param object_name: Folder to which chunks will be uploaded
        :return: True if all chunks were uploaded successfully, False if not
        """
        if not os.path.exists(file_name):
            raise Exception("file_name does not exist")
        if not os.path.isfile(file_name):
            raise Exception("file_name must be file")

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        # open file to chunk
        with open(file_name, "rb") as f:
            part_num = 0
            all_chunks_uploaded = True
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_stream = io.BytesIO(chunk)
                chunk_name = get_chunk_file_name(part_num)
                chunk_object_name = object_name + "/" + chunk_name
                part_num = part_num + 1
                # Upload the file
                try:
                    response = self._client.upload_fileobj(
                        chunk_stream, bucket, chunk_object_name)
                except ClientError as e:
                    logging.error(e)
                    all_chunks_uploaded = False
                chunk_stream.close()
            return all_chunks_uploaded

    def download_file_from_chunks(self, bucket, object_name, file_name=None):
        """
        Download chunks from S3 bucket, assemble them into file
        :param file_name: path to file that will be downloaded to
        :param bucket: Bucket to download from
        :param object_name: directory that chunks are stored in
        :return: True if all chunks download successfully, False otherwise
        """

        # if file_name was not specified, use object_name
        if file_name is None:
            file_name = object_name

        if not os.path.exists(os.path.dirname(file_name)):
            os.makedirs(os.path.dirname(file_name))

        part_num = 0
        all_chunks_downloaded = True
        with open(file_name, "wb") as f:
            while True:
                with io.BytesIO() as chunk_stream:
                    chunk_name = get_chunk_file_name(part_num)
                    chunk_object_name = object_name + "/" + chunk_name
                    part_num = part_num + 1
                    try:
                        response = self._client.download_fileobj(
                            bucket, chunk_object_name, chunk_stream)
                    except ClientError as e:
                        if e.response['Error']['Code'] == '404':
                            break
                        else:
                            logging.error(e)
                            all_chunks_downloaded = False
                    f.write(chunk_stream.getvalue())
        return all_chunks_downloaded


    def upload_file(self, file_name, bucket, object_name=None):
        """Upload a file to an S3 bucket
        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. 
            If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        # Upload the file
        try:
            response = self._client.upload_file(
                    file_name, bucket, object_name,
                    Callback=ProgressPercentageUpload(file_name))
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def download_file(self, file_name, bucket, object_name):
        self._client.download_file(
                bucket, object_name, file_name,
                Callback=ProgressPercentageDownload(
                    self._client, bucket, file_name, object_name))
                

    def download_folder(self, bucket_name, folder_prefix, out_dir):
        bucket = boto3.resource('s3').Bucket(bucket_name)
        for file_object in bucket.objects.filter(Prefix=folder_prefix):
            object_name = file_object.key
            print(object_name)
            file_name = os.path.join(out_dir, object_name)
            make_dirs(os.path.dirname(file_name))
            self.download_file(file_name, bucket_name, object_name)
