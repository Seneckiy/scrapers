import urllib.request
import boto3
import os
from botocore.exceptions import ClientError

BUCKET_NAME = os.environ['bucket_name']
AWS_ACCESS_KEY = os.environ['aws_access_key']
AWS_SECRET_KEY = os.environ['aws_secret_key']


def _get_client():

    s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name='us-east-2'
        )
    print(s3.get_bucket_location(Bucket=BUCKET_NAME))
    return s3


def get_image_link_s3(link, image_id):

    s3 = _get_client()
    response = urllib.request.urlopen(link)
    image = response.read()
    s3.put_object(ACL='public-read', Body=image, Bucket=BUCKET_NAME, Key=image_id)
    image_link = '{}/{}/{}'.format(s3.meta.endpoint_url, BUCKET_NAME, image_id)
    return image_link


def check_mall_image(link, mall_name):
    s3 = _get_client()

    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=mall_name)
        image_link = '{}/{}/{}'.format(s3.meta.endpoint_url, BUCKET_NAME, mall_name)
    except ClientError:
        response = urllib.request.urlopen(link)
        image = response.read()
        s3.put_object(ACL='public-read', Body=image, Bucket=BUCKET_NAME, Key=mall_name)
        image_link = '{}/{}/{}'.format(s3.meta.endpoint_url, BUCKET_NAME, mall_name)
    return image_link
