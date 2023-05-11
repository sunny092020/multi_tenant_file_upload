import pytest

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mtfu.settings")
django.setup()

from rest_framework.test import APIClient
from mtfu.auth_user.models import Tenant
from mtfu.file_manager.models import File


@pytest.fixture
def api_client():
    # Create a test user
    user = Tenant.create("john1", "mypassword")

    token_data = {
        "username": user.username,
        "password": "mypassword",
    }
    token_response = APIClient().post("/api/token/", data=token_data)

    token = token_response.data["access"]

    # Create an authenticated test client using the JWT token
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    return client


@pytest.fixture
def tmp_files(tmp_path):
    # Generate files with different names and content
    files = []
    for i in range(3):
        file_path = tmp_path / f"test_file_{i}.txt"
        with open(file_path, "w") as f:
            f.write(f"test content {i}")
        files.append(file_path)
    return files


def test_upload_tmp_files(tmp_files, api_client):
    # Upload the files
    for file_path in tmp_files:
        with open(file_path, "rb") as file:
            response = api_client.post(
                "/api/upload",
                {
                    "file": file,
                    "resource": "product",
                    "resource_id": 1,
                },
            )
            assert response.status_code == 200

    # Verify that the files were uploaded
    assert File.objects.count() == 3
    for file_path in tmp_files:
        file_name = os.path.basename(file_path)
        assert File.objects.filter(name=file_name).exists()

    # verify GET files/<str:resource>/<str:resourceId> endpoint
    response = api_client.get("/api/files/product/1")
    assert response.status_code == 200

    response_files = response.data["files"]

    assert len(response_files) == 3
    assert response_files[0]["name"] == "test_file_0.txt"
    assert response_files[1]["name"] == "test_file_1.txt"
    assert response_files[2]["name"] == "test_file_2.txt"

    assert response_files[0]["location"] == "asset_imgs/john1/test_file_0.txt"
    assert response_files[1]["location"] == "asset_imgs/john1/test_file_1.txt"
    assert response_files[2]["location"] == "asset_imgs/john1/test_file_2.txt"

    # verify file records are not deleted
    assert (
        File.objects.filter(
            delete_flg=False,
        ).count()
        == 3
    )

    # verify DELETE files/<str:resource>/<str:resourceId> endpoint
    response = api_client.delete("/api/files/product/1")
    assert response.status_code == 200

    # verify file records are deleted
    assert (
        File.objects.filter(
            delete_flg=False,
        ).count()
        == 0
    )

    # verify GET files/<str:resource>/<str:resourceId> endpoint after delete
    response = api_client.get("/api/files/product/1")
    assert response.status_code == 200

    response_files = response.data["files"]
    assert len(response_files) == 0


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
