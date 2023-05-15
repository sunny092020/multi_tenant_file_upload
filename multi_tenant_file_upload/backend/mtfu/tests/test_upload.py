import pytest

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mtfu.settings")
django.setup()

from rest_framework.test import APIClient
from mtfu.auth_user.models import Tenant
from mtfu.file_manager.models import File
from django.test import override_settings


@pytest.fixture
def john():
    return Tenant.create("john", "mypassword")


@pytest.fixture
def jimmy():
    return Tenant.create("jimmy", "mypassword")


@pytest.fixture
def john_client(john):
    return api_client(john)


@pytest.fixture
def jimmy_client(jimmy):
    return api_client(jimmy)


def api_client(tenant):
    token_data = {
        "username": tenant.username,
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


@pytest.fixture
def tmp_file(tmp_path):
    file_path = tmp_path / "test_file.txt"
    with open(file_path, "w") as f:
        f.write("test content")
    return file_path


def test_upload_tmp_files(tmp_files, john_client):
    # Upload the files
    for file_path in tmp_files:
        with open(file_path, "rb") as file:
            response = john_client.post(
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
    response = john_client.get("/api/files/product/1")
    assert response.status_code == 200

    response_files = response.data["files"]

    assert len(response_files) == 3
    assert response_files[0]["name"] == "test_file_0.txt"
    assert response_files[1]["name"] == "test_file_1.txt"
    assert response_files[2]["name"] == "test_file_2.txt"

    assert response_files[0]["location"] == "asset_imgs/john/test_file_0.txt"
    assert response_files[1]["location"] == "asset_imgs/john/test_file_1.txt"
    assert response_files[2]["location"] == "asset_imgs/john/test_file_2.txt"

    # verify file records are not deleted
    assert (
        File.objects.filter(
            delete_flg=False,
        ).count()
        == 3
    )

    # verify DELETE files/<str:resource>/<str:resourceId> endpoint
    response = john_client.delete("/api/files/product/1")
    assert response.status_code == 200

    # verify file records are deleted
    assert (
        File.objects.filter(
            delete_flg=False,
        ).count()
        == 0
    )

    # verify GET files/<str:resource>/<str:resourceId> endpoint after delete
    response = john_client.get("/api/files/product/1")
    assert response.status_code == 200

    response_files = response.data["files"]
    assert len(response_files) == 0


def test_upload_with_authorized_user(john_client):
    fileUploadPath = os.path.join(os.path.dirname(__file__), "test_file")

    # verify no file record exists
    assert File.objects.count() == 0

    with open(fileUploadPath, "rb") as file:
        response = john_client.post(
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
            tenant__username="john",
        ).count()
        == 1
    )


def test_upload_with_unauthorized_user():
    fileUploadPath = os.path.join(os.path.dirname(__file__), "test_file")
    with open(fileUploadPath, "rb") as file:
        response = APIClient().post("/api/upload", {"file": file})
        assert response.status_code == 401


def test_retrieve_files_with_unauthorized_user():
    response = APIClient().get("/api/files/product/1")
    assert response.status_code == 401


def test_delete_files_with_unauthorized_user():
    response = APIClient().delete("/api/files/product/1")
    assert response.status_code == 401


def test_list_files_with_unauthorized_user():
    response = APIClient().get("/api/list_files")
    assert response.status_code == 401


def test_list_files(john_client, jimmy_client, tmp_file):
    with open(tmp_file, "rb") as file:
        john_client.post(
            "/api/upload",
            {
                "file": file,
                "resource": "avatar",
                "resource_id": 1,
            },
        )

        john_client.post(
            "/api/upload",
            {
                "file": file,
                "resource": "product",
                "resource_id": 2,
            },
        )

        jimmy_client.post(
            "/api/upload",
            {
                "file": file,
                "resource": "avatar",
                "resource_id": 2,
            },
        )

        jimmy_client.post(
            "/api/upload",
            {
                "file": file,
                "resource": "product",
                "resource_id": 1,
            },
        )

    # verify GET list_files/ by john
    response = john_client.get("/api/list_files", {"tenant_username": "john"})
    response_files = response.data["files"]

    for file in response_files:
        assert file["tenant"] == "john"

    # verify GET list_files/ by jimmy
    response = jimmy_client.get("/api/list_files", {"tenant_username": "jimmy"})
    response_files = response.data["files"]

    for file in response_files:
        assert file["tenant"] == "jimmy"

    # verify GET list_files/ by resource product
    response = john_client.get("/api/list_files", {"resource": "product"})
    response_files = response.data["files"]

    for file in response_files:
        assert file["resource"] == "product"

    # verify GET list_files/ by resource avatar
    response = john_client.get("/api/list_files", {"resource": "avatar"})
    response_files = response.data["files"]

    for file in response_files:
        assert file["resource"] == "avatar"

    # verify GET list_files/ by resource product and tenant john
    response = john_client.get(
        "/api/list_files",
        {
            "resource": "product",
            "tenant_username": "john",
        },
    )
    response_files = response.data["files"]

    for file in response_files:
        assert file["resource"] == "product"
        assert file["tenant"] == "john"

    # verify GET list_files/ by resource id 1
    response = john_client.get("/api/list_files", {"resource_id": 1})
    response_files = response.data["files"]

    for file in response_files:
        assert file["resource_id"] == "1"

    # verify GET list_files/
    response = john_client.get("/api/list_files")
    response_files = response.data["files"]

    assert len(response_files) == 2


@pytest.fixture
def bigger_than_10mb_file(tmp_path):
    file_path = tmp_path / "bigger_than_10mb_file.txt"
    file_path.write_text("a" * 1024 * 1024 * 11)
    return file_path


def test_upload_file_bigger_than_10mb(john_client, bigger_than_10mb_file):
    with open(bigger_than_10mb_file, "rb") as file:
        response = john_client.post(
            "/api/upload",
            {
                "file": file,
                "resource": "product",
                "resource_id": 1,
            },
        )
        assert response.status_code == 400


def test_upload_without_file(john_client):
    response = john_client.post(
        "/api/upload",
        {
            "resource": "product",
            "resource_id": 1,
        },
    )
    assert response.status_code == 400
    assert response.data["message"] == "['No file was submitted.']"


def test_upload_without_resource(john_client, tmp_file):
    with open(tmp_file, "rb") as file:
        response = john_client.post(
            "/api/upload",
            {
                "file": file,
                "resource_id": 1,
            },
        )
        assert response.status_code == 400
        assert response.data["message"] == "['No resource found']"


def test_upload_without_resource_id(john_client, tmp_file):
    with open(tmp_file, "rb") as file:
        response = john_client.post(
            "/api/upload",
            {
                "file": file,
                "resource": "product",
            },
        )
        assert response.status_code == 400
        assert response.data["message"] == "['No resource id found']"


def test_retrieve_file_without_resource_id(john_client):
    response = john_client.get("/api/files/product")
    assert response.status_code == 404


def test_retrieve_file_without_resource(john_client):
    response = john_client.get("/api/files/1")
    assert response.status_code == 404


def test_retrieve_file_without_resource_id_and_resource(john_client):
    response = john_client.get("/api/files")
    assert response.status_code == 404


def test_delete_file_without_resource_id(john_client):
    response = john_client.delete("/api/files/product")
    assert response.status_code == 404


def test_delete_file_without_resource(john_client):
    response = john_client.delete("/api/files/1")
    assert response.status_code == 404


def test_delete_file_without_resource_id_and_resource(john_client):
    response = john_client.delete("/api/files")
    assert response.status_code == 404


def test_user_upload_the_same_file_twice(john_client, tmp_file):
    with open(tmp_file, "rb") as file:
        response = john_client.post(
            "/api/upload",
            {
                "file": file,
                "resource": "product",
                "resource_id": 1,
            },
        )
        assert response.status_code == 200

        response = john_client.post(
            "/api/upload",
            {
                "file": file,
                "resource": "product",
                "resource_id": 1,
            },
        )
        assert response.status_code == 200


def test_pagination(john_client, tmp_file):
    for i in range(1, 11):
        with open(tmp_file, "rb") as file:
            response = john_client.post(
                "/api/upload",
                {
                    "file": file,
                    "resource": "product",
                    "resource_id": i,
                },
            )
            assert response.status_code == 200

    response = john_client.get("/api/list_files", {"page": 1, "page_size": 3})
    response_files = response.data["files"]
    assert len(response_files) == 3

    response = john_client.get("/api/list_files", {"page": 2, "page_size": 5})
    response_files = response.data["files"]
    assert len(response_files) == 5

    response = john_client.get("/api/list_files", {"page": 4, "page_size": 3})
    response_files = response.data["files"]
    assert len(response_files) == 1


def test_file_upload_invalid(john_client):
    response = john_client.post(
        "/api/upload",
        {
            "file": "invalid",
            "resource": "product",
            "resource_id": 1,
        },
    )
    assert response.status_code == 400
    assert response.data["message"] == "['Invalid file']"


@pytest.fixture
def ten_tmp_files(tmp_path):
    # Generate files with different names and content
    files = []
    for i in range(10):
        file_path = tmp_path / f"test_file_{i}.txt"
        with open(file_path, "w") as f:
            f.write(f"test content {i}")
        files.append(file_path)
    return files


# test pagination with retrieve files GET "/api/files/{resource}/{resource_id}"
def test_pagination_with_retrieve_files(john_client, ten_tmp_files):
    for file in ten_tmp_files:
        response = john_client.post(
            "/api/upload",
            {
                "file": open(file, "rb"),
                "resource": "product",
                "resource_id": 1,
            },
        )
        assert response.status_code == 200

    response = john_client.get("/api/files/product/1?page=1&page_size=3")
    response_files = response.data["files"]
    assert len(response_files) == 3

    response = john_client.get("/api/files/product/1?page=2&page_size=5")
    response_files = response.data["files"]
    assert len(response_files) == 5

    response = john_client.get("/api/files/product/1?page=4&page_size=3")
    response_files = response.data["files"]
    assert len(response_files) == 1
