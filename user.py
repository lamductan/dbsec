import os
import logging
import boto3
from botocore.exceptions import ClientError

from utils import ProgressPercentageUpload, ProgressPercentageDownload


class User(object):
    
    def __init__(self, aws_credential_path="~/.aws/credentials"):
        self._aws_credential_path = aws_credential_path
        self._client = boto3.client('s3')

    def get_list_bucket(self):
        reponse = self._client.list_buckets()
        return reponse['Buckets']

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
                    self._client, bucket, object_name))
                
