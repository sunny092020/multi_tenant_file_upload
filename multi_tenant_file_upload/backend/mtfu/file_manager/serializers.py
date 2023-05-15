from rest_framework import serializers
from django.conf import settings
from mtfu.file_manager.s3_utils import get_s3_client
from mtfu.file_manager.models import File


class FileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    tenant_username = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "tenant_username",
            "resource",
            "resource_id",
            "name",
            "location",
            "expire_at",
            "is_public",
            "url",
        ]

    def __init__(self, *args, **kwargs):
        # get 'fields' passed in
        chosen_fields = kwargs.pop("fields", None)

        # Initialize the superclass as usual
        super(FileSerializer, self).__init__(*args, **kwargs)

        if chosen_fields is not None:
            # Only keep the fields specified in the 'fields' argument
            valid_fields = set(chosen_fields)

            # all default fields
            current_fields = set(self.fields)

            # remove fields which are not specified in the 'fields' argument
            for field_name in current_fields - valid_fields:
                self.fields.pop(field_name)

    def get_url(self, obj):
        # Use an S3 client to generate a presigned URL for the file
        s3_client = get_s3_client()
        return s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Key": obj.location,
            },
            ExpiresIn=settings.AWS_S3_PRESIGNED_URLS_EXPIRE,
        )

    def get_tenant_username(self, obj):
        return obj.tenant.username
