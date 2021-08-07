from botocore.exceptions import ClientError
import boto3

import foo


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=foo.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=foo.AWS_SECRET_ACCESS_KEY,
    )


def upload_file(file_name, object_name=None):
    if object_name is None:
        object_name = file_name

    s3_client = get_s3_client()
    try:
        _response = s3_client.upload_file(file_name, foo.S3_BUCKET_NAME, object_name)
    except ClientError as _exc:
        return False
    return True


def create_presigned_url(object_name, expiration=foo.S3_URL_EXPIRE_AFTER):
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            'get_object', Params={
                'Bucket': foo.S3_BUCKET_NAME, 'Key': object_name
            }, ExpiresIn=expiration
        )
    except ClientError as _exc:
        return None

    return response
