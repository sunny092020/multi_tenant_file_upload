from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status

from django.conf import settings
from botocore.exceptions import ClientError
from mtfu.file_manager.models import File
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from mtfu.file_manager.s3_utils import get_s3_client
from mtfu.file_manager.pagination_utils import paginate_files
import logging

logger = logging.getLogger(__name__)


class UploadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]

    def post(self, request):
        try:
            upload_file, resource, resource_id = self._extract_data(request)
            self._validate_data(upload_file, resource, resource_id)
        except ValidationError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        s3_client = get_s3_client()
        user = request.user
        file_location = f"{settings.ASSET_IMAGE_FOLDER}/{user.username}/{upload_file.name}"

        try:
            self._upload_file_to_s3(upload_file, s3_client, file_location)
        except ClientError as e:
            logger.error(e)
            return Response(
                {"message": "File upload failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            self._create_file_object(
                user, upload_file.name, resource, resource_id, file_location
            )
        except Exception as e:
            logger.error(e)
            # remove uploaded file from s3
            s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_location)
            return Response(
                {"message": "File save failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "File uploaded successfully"})

    def _extract_data(self, request):
        data = request.data
        upload_file = data.get("file")
        resource = data.get("resource")
        resource_id = data.get("resource_id")
        return upload_file, resource, resource_id

    def _validate_data(self, upload_file, resource, resource_id):
        if not upload_file:
            raise ValidationError("No file was submitted.")

        if not hasattr(upload_file, "size"):
            raise ValidationError("Invalid file")

        max_file_size = settings.MAX_FILE_SIZE
        if upload_file.size > max_file_size:
            raise ValidationError(
                f"File size exceeds the maximum allowed size of {max_file_size} bytes"
            )

        if not resource:
            raise ValidationError("No resource found")

        if not resource_id:
            raise ValidationError("No resource id found")

    def _upload_file_to_s3(self, upload_file, s3_client, file_location):
        s3_client.upload_fileobj(
            upload_file,
            settings.AWS_STORAGE_BUCKET_NAME,
            file_location,
        )

    def _create_file_object(self, user, filename, resource, resource_id, file_location):
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


class FileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, resource, resourceId):
        # get user from session
        user = request.user

        files = File.objects.filter(
            Q(tenant=user) | Q(is_public=True),
            resource=resource,
            resource_id=resourceId,
            delete_flg=False,
            expire_at__gte=timezone.now(),
        )

        returned_fields = [
            "tenant_username",
            "resource",
            "resource_id",
            "name",
            "location",
            "expire_at",
            "is_public",
            "url",
        ]
        data = paginate_files(request, files, returned_fields)
        return Response(data)

    @transaction.atomic
    def delete(self, request, resource, resourceId):
        # get user from session
        user = request.user

        files = File.objects.filter(
            tenant=user,
            resource=resource,
            resource_id=resourceId,
            delete_flg=False,
        )

        for file in files:
            file.delete_flg = True
            file.save()

        return Response({"message": "File deleted successfully"})


class ListFilesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # get user from session
        user = request.user
        files = File.objects.filter(
            Q(tenant=user) | Q(is_public=True),
            delete_flg=False,
            expire_at__gte=timezone.now(),
        )

        tenant_username = request.GET.get("tenant_username", None)
        if tenant_username is not None:
            files = files.filter(tenant__username=tenant_username)

        resource = request.GET.get("resource", None)
        if resource is not None:
            files = files.filter(resource=resource)

        resource_id = request.GET.get("resource_id", None)
        if resource_id is not None:
            files = files.filter(resource_id=resource_id)

        returned_fields = [
            "tenant_username",
            "resource",
            "resource_id",
            "name",
            "location",
            "expire_at",
            "is_public",
        ]
        data = paginate_files(request, files, returned_fields)
        return Response(data)
