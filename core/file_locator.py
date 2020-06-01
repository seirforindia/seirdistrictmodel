import pandas as pd
from datetime import datetime
import json
import boto3
from botocore.exceptions import NoCredentialsError

ACCESS_KEY = 'AKIAIORXV5HQEGT2JXUQ'
SECRET_KEY = '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'

OPTIMIZER_ACCESS_KEY="AKIAILZCROEDWJUN2O6A"
OPTIMIZER_BUCKET_NAME="covid19-seir-plus-optimizer"
OPTIMIZER_SECRET_KEY="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"

DISTRICT_STATS = 'district_stats.json'
STATE_STATS = 'state_stats.json'
MAP_STATE = 'state_map_data.csv'
DATA_DIR = 'data'
BUCKET_DIR = 'optimizer_data'

FIRSTJAN = datetime(2020,1,1,0,0,0,0)


def upload_to_aws(local_file, bucket, s3_file, aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY):
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key)
    try:
        s3_client.upload_file(local_file, bucket, s3_file)
        print("Upload Successful: " + s3_file)
        return True
    except FileNotFoundError:
        print("The file was not found: "+ s3_file)
        return False
    except NoCredentialsError:
        print("Credentials not available: "+ s3_file)
        return False

def download_from_aws(aws_access_key_id=OPTIMIZER_ACCESS_KEY,
                      aws_secret_access_key=OPTIMIZER_SECRET_KEY):
    s3_res_bucket = boto3.resource('s3', aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key).Bucket(OPTIMIZER_BUCKET_NAME)
    try:
        s3_res_bucket.download_file(f"{BUCKET_DIR}/{DISTRICT_STATS}",
                                    f"{DATA_DIR}/{DISTRICT_STATS}")
        print(f'downloaded {DISTRICT_STATS}')
        s3_res_bucket.download_file(f"{BUCKET_DIR}/{STATE_STATS}",
                                    f"{DATA_DIR}/{STATE_STATS}")
        print(f'downloaded {STATE_STATS}')
        s3_res_bucket.download_file(f"{BUCKET_DIR}/{MAP_STATE}",
                                    f"{DATA_DIR}/{MAP_STATE}")
        print(f'downloaded {MAP_STATE}')
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False
    except e:
        print(e)

def get_district_stats():
    with open(f"{DATA_DIR}/{DISTRICT_STATS}") as district_robj:
        return json.loads(district_robj.read())

def get_state_stats():
    with open(f"{DATA_DIR}/{STATE_STATS}") as state_robj:
         return json.loads(state_robj.read())

def get_state_map_data():
    state_map = pd.read_csv(f'{DATA_DIR}/{MAP_STATE}')
    state_map['Reported'] = pd.to_datetime(state_map['Reported'], format='%Y-%m-%d')
    return state_map
