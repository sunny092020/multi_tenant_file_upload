from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status

from mtfu.file_manager.models import File
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from mtfu.file_manager.pagination_utils import paginate_files
from mtfu.file_manager.serializers import UploadSerializer
import logging

logger = logging.getLogger(__name__)


class UploadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]

    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        if serializer.is_valid():
            upload_file = serializer.validated_data["file"]
            resource = serializer.validated_data["resource"]
            resource_id = serializer.validated_data["resource_id"]

            try:
                File.create(request.user, upload_file, resource, resource_id)
            except ValueError as e:
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "File uploaded successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
