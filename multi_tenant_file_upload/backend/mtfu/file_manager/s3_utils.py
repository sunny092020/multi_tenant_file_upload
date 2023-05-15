import boto3
from django.conf import settings

S3_SESSION = boto3.session.Session(
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)


def get_s3_client():
    return S3_SESSION.client("s3")
