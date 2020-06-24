from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError

FIRSTJAN = datetime(2020, 1, 1, 0, 0, 0, 0)

class FileLoader:

    def __init__(self, env_resolver, resource_config):
        self.access_key = env_resolver['env_variables.ACCESS_KEY']
        self.secret_key = env_resolver['env_variables.SECRET_KEY']
        self.optimizer_access_key = env_resolver['env_variables.OPTIMIZER_ACCESS_KEY']
        self.optimizer_secret_key = env_resolver['env_variables.OPTIMIZER_SECRET_KEY']
        self.bucket_dir = resource_config.get('BUCKET', 'BUCKET_DIR')
        self.district_stats = resource_config.get('STATS', 'DISTRICT_STATS')
        self.state_stats = resource_config.get('STATS', 'STATE_STATS')
        self.data_dir = resource_config.get('PATH', 'DATA_DIR')
        self.optimizer_bucket_name = resource_config.get('BUCKET', 'OPTIMIZER_BUCKET_NAME')
        self.map_state = resource_config.get('STATS', 'MAP_STATE')

    @staticmethod
    def upload_to_aws(local_file, bucket, s3_file,access_key,secret_key):
        s3_client = boto3.client('s3', aws_access_key_id=access_key,
                                 aws_secret_access_key=secret_key)
        try:
            s3_client.upload_file(local_file, bucket, s3_file)
            print("Upload Successful: " + s3_file)
            return True
        except FileNotFoundError:
            print("The file was not found: " + s3_file)
            return False
        except NoCredentialsError:
            print("Credentials not available: " + s3_file)
            return False


    def download_from_aws(self):
        s3_res_bucket = boto3.resource('s3', aws_access_key_id=self.access_key,
                                       aws_secret_access_key=self.secret_key).Bucket(self.optimizer_bucket_name)
        try:
            s3_res_bucket.download_file(f"{self.bucket_dir}/{self.district_stats}",
                                        f"{self.data_dir}/{self.district_stats}")
            print(f'downloaded {self.district_stats}')
            s3_res_bucket.download_file(f"{self.bucket_dir}/{self.state_stats}",
                                        f"{self.data_dir}/{self.state_stats}")
            print(f'downloaded {self.state_stats}')
            s3_res_bucket.download_file(f"{self.bucket_dir}/{self.map_state}",
                                        f"{self.data_dir}/{self.map_state}")
            print(f'downloaded {self.map_state}')
        except FileNotFoundError:
            print("The file was not found")
            return False
        except NoCredentialsError:
            print("Credentials not available")
            return False
        except Exception as e:
            print(e)