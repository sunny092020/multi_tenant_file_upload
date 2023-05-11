from .views import UploadView, FileView
from django.urls import path

urlpatterns = [
    path("upload", UploadView.as_view(), name="mtfu.upload"),
    path("files/<str:resource>/<str:resourceId>", FileView.as_view(), name="mtfu.files"),
]
