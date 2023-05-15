from django.db import models
from mtfu.auth_user.models import Tenant
from mtfu.file_manager.s3_utils import get_s3_client
from django.conf import settings
from dateutil.relativedelta import relativedelta
from botocore.exceptions import ClientError
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class File(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False, null=False)
    location = models.CharField(max_length=100, blank=False, null=False)
    expire_at = models.DateTimeField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    resource = models.CharField(max_length=100, blank=True, null=True)
    resource_id = models.CharField(max_length=100, blank=True, null=True)
    delete_flg = models.BooleanField(default=False)

    class Meta:
        db_table = "file"
        unique_together = ("tenant", "name", "resource", "resource_id")

    @classmethod
    def create(cls, user, upload_file, resource, resource_id):
        s3_client = get_s3_client()
        file_location = f"{settings.ASSET_IMAGE_FOLDER}/{user.username}/{upload_file.name}"

        try:
            cls._upload_file_to_s3(upload_file, s3_client, file_location)
        except ClientError as e:
            logger.error(e)
            raise ValueError("File upload failed")

        try:
            cls._create_file_object(
                user, upload_file.name, resource, resource_id, file_location
            )
        except Exception as e:
            logger.error(e)
            # Remove uploaded file from S3
            s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_location)
            raise ValueError("File save failed")

    @staticmethod
    def _upload_file_to_s3(upload_file, s3_client, file_location):
        s3_client.upload_fileobj(upload_file, settings.AWS_STORAGE_BUCKET_NAME, file_location)

    @staticmethod
    def _create_file_object(user, filename, resource, resource_id, file_location):
        tomorrow = timezone.now() + relativedelta(days=1)

        defaults = {
            "expire_at": tomorrow,
            "location": file_location,
        }
        File.objects.update_or_create(
            tenant=user,
            resource=resource,
            resource_id=resource_id,
            name=filename,
            defaults=defaults,
        )
