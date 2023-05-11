from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import boto3
from django.conf import settings
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
        filename = upload_file.name
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        # get user from session
        user = request.user

        file_location = f"{settings.ASSET_IMAGE_FOLDER}/{user.username}/{filename}"

        try:
            s3_client.upload_fileobj(
                upload_file,
                settings.AWS_STORAGE_BUCKET_NAME,
                file_location,
            )
        except ClientError as e:
            print(e)
            return

        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

        file = File(
            name=filename,
            resource=resource,
            resource_id=resource_id,
            tenant=user,
            location=file_location,
            expire_at=tomorrow,
        )
        file.save()

        return Response({"message": "File uploaded successfully"})


class FileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, resource, resourceId):
        # get user from session
        user = request.user

        files = File.objects.filter(tenant=user, resource=resource, resource_id=resourceId, delete_flg=False)

        file_list = []
        for file in files:
            file_list.append(
                {
                    "name": file.name,
                    "location": file.location,
                    "expire_at": file.expire_at,
                    "is_public": file.is_public,
                }
            )

        return Response({"files": file_list})
