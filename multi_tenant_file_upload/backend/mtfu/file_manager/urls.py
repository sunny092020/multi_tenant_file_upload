from .views import UploadView
from django.urls import path

urlpatterns = [
    path("upload", UploadView.as_view(), name="mtfu.upload"),
]
