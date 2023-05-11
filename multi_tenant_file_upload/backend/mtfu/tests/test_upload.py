import pytest

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mtfu.settings")
django.setup()

from rest_framework.test import APIClient
from mtfu.auth_user.models import Tenant
from mtfu.file_manager.models import File
import datetime

@pytest.fixture
def api_client():
    # Create a test user
    user = Tenant(
        username="john1",
    )
    user.set_password("mypassword")
    user.save()

    token_data = {
        "username": "john1",
        "password": "mypassword",
    }
    token_response = APIClient().post("/api/token/", data=token_data)

    token = token_response.data["access"]

    # Create an authenticated test client using the JWT token
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    return client


def test_upload_with_authorized_user(api_client):
    fileUploadPath = os.path.join(os.path.dirname(__file__), "test_file")

    # verify no file record exists
    assert File.objects.count() == 0

    with open(fileUploadPath, "rb") as file:
        response = api_client.post(
            "/api/upload",
            {
                "file": file,
                "resource": "product",
                "resource_id": 1,
            },
        )
        assert response.status_code == 200

    # verify file record exists
    assert (
        File.objects.filter(
            name="test_file",
            resource="product",
            resource_id=1,
            tenant__username="john1",
        ).count()
        == 1
    )


def test_upload_with_unauthorized_user():
    fileUploadPath = os.path.join(os.path.dirname(__file__), "test_file")
    with open(fileUploadPath, "rb") as file:
        response = APIClient().post("/api/upload", {"file": file})
        assert response.status_code == 401
