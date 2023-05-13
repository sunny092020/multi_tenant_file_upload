from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status

import boto3
from django.conf import settings
from botocore.exceptions import ClientError
from mtfu.file_manager.models import File
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError


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

        s3_client = self._get_s3_client()
        user = request.user
        file_location = f"{settings.ASSET_IMAGE_FOLDER}/{user.username}/{upload_file.name}"

        try:
            self._upload_file_to_s3(upload_file, s3_client, file_location)
        except ClientError as e:
            print(e)
            return Response(
                {"message": "File upload failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            self._create_file_object(
                user, upload_file.name, resource, resource_id, file_location
            )
        except Exception as e:
            print(e)
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

    def _get_s3_client(self):
        return boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

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

        data = paginate_files(request, files)
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

    def post(self, request):
        # get user from session
        user = request.user
        files = File.objects.filter(
            Q(tenant=user) | Q(is_public=True),
            delete_flg=False,
            expire_at__gte=timezone.now(),
        )

        if "tenant_username" in request.POST:
            tenant_username = request.POST["tenant_username"]
            files = files.filter(tenant__username=tenant_username)

        if "resource" in request.POST:
            resource = request.POST["resource"]
            files = files.filter(resource=resource)

        if "resource_id" in request.POST:
            resource_id = request.POST["resource_id"]
            files = files.filter(resource_id=resource_id)

        data = paginate_files(request, files)
        return Response(data)


def paginate_files(request, files):
    page_number = request.POST.get("page", 1)
    page_size = request.POST.get("page_size", 10)

    files = files.order_by("name")

    paginator = Paginator(files, page_size)
    try:
        file_list = paginator.page(page_number)
    except PageNotAnInteger:
        file_list = paginator.page(1)
    except EmptyPage:
        file_list = paginator.page(paginator.num_pages)

    # Return serialized data with pagination information
    data = {
        "count": paginator.count,
        "num_pages": paginator.num_pages,
        "page_range": list(paginator.page_range),
        "files": [
            {
                "tenant": file.tenant.username,
                "resource": file.resource,
                "resource_id": file.resource_id,
                "name": file.name,
                "location": file.location,
                "expire_at": file.expire_at,
                "is_public": file.is_public,
            }
            for file in file_list
        ],
    }
    return data
