from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import UserManager
import boto3
from django.conf import settings
from botocore.exceptions import ClientError


class Tenant(AbstractBaseUser):
    username = models.CharField(max_length=20, blank=False, null=False, unique=True)
    password = models.CharField(max_length=128)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        managed = True
        unique_together = (("username",),)

    @classmethod
    def create(cls, username, password):
        # create a folder for the tenant in S3
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        try:
            s3_client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=settings.ASSET_IMAGE_FOLDER + "/" + username + "/",
            )
        except ClientError as e:
            return
        
        tenant = cls(username=username)
        tenant.set_password(password)
        tenant.save()

        return tenant
