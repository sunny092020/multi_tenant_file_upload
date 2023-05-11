from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import boto3
from django.conf import settings
import uuid
from botocore.exceptions import ClientError
from mtfu.file_manager.models import File
import datetime
from django.db import transaction

class UploadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]

    @transaction.atomic
    def post(self, request):
        upload_file = request.data["file"]
        resource = request.data["resource"]
        resource_id = request.data["resource_id"]

        # Uploading the image to S3
        filename_versioning = versioning_filename(filename=upload_file.name)
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        try:
            s3_client.upload_fileobj(
                upload_file,
                settings.AWS_STORAGE_BUCKET_NAME,
                settings.ASSET_IMAGE_FOLDER + "/" + filename_versioning,
            )
        except ClientError as e:
            return
        
        # get user from session
        user = request.user

        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

        file = File(
            name=filename_versioning,
            resource=resource,
            resource_id=resource_id,
            tenant=user,
            location=settings.ASSET_IMAGE_FOLDER + "/" + filename_versioning,
            expire_at=tomorrow
        )
        file.save()

        return Response({"message": "File uploaded successfully"})


def versioning_filename(filename):
    ext = filename.split(".")[-1]
    name = filename.split(".")[0]
    filename = "{}-{}.{}".format(name, uuid.uuid1().hex[:8], ext)
    return filename
