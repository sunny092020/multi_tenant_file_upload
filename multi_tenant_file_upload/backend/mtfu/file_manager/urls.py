from .views import UploadView, FileView, ListFilesView
from django.urls import path

urlpatterns = [
    path("upload", UploadView.as_view(), name="mtfu.upload"),
    path(
        "files/<str:resource>/<str:resourceId>",
        FileView.as_view(),
        name="mtfu.files",
    ),
    path("list_files", ListFilesView.as_view(), name="mtfu.list_files"),
]
