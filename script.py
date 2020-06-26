import os
import boto3
import json

BUCKET_NAME=""
OPTIMIZER_BUCKET_NAME=""
FLOURISH_BUCKET=""

ACCESS_KEY = os.environ["ACCESS_KEY"]
SECRET_KEY = os.environ["SECRET_KEY"]


s3client = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    #aws_session_token=SESSION_TOKEN
)
response = s3client.list_buckets()


for bucket in [BUCKET_NAME,OPTIMIZER_BUCKET_NAME]:
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'AddPerm',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            'Resource': f'arn:aws:s3:::{bucket}/*'
        }]
    }
    bucket_policy = json.dumps(bucket_policy)
    s3client.create_bucket(Bucket=bucket)
    s3client.put_bucket_policy(Bucket=bucket, Policy=bucket_policy)

print("create successfully")
print("Update these buckets in config/resource.ini")
print("BUCKET_DIR="+BUCKET_NAME)
print("OPTIMIZER_BUCKET_NAME="+OPTIMIZER_BUCKET_NAME)
print("FLOURISH_BUCKET_DIR="+FLOURISH_BUCKET)
