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
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.utils import timezone


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

        files = File.objects.filter(tenant=user, resource=resource, resource_id=resourceId, delete_flg=False)

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
        files = File.objects.filter(Q(tenant=user) | Q(is_public=True), delete_flg=False, expire_at__gte=timezone.now())

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
    # Get pagination parameters from query parameters, or use defaults if not provided
    page_number = request.GET.get("page", 1)
    page_size = request.GET.get("page_size", 10)

    paginator = Paginator(files, page_size)
    try:
        file_list = paginator.page(page_number)
    except PageNotAnInteger:
        # If page_number is not an integer, deliver first page.
        file_list = paginator.page(1)
    except EmptyPage:
        # If page_number is out of range (e.g. 9999), deliver last page of results.
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
