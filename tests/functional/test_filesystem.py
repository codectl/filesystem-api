import io
from base64 import b64encode

import pytest

from src.services.auth import AuthSvc


@pytest.fixture()
def auth(mocker):
    mocker.patch.object(AuthSvc, "authenticate", return_value=True)
    return {"Authorization": f"Basic {b64encode(b'user:pass').decode()}"}


class TestFilesystemGET:
    def test_unauthorized_request_throws_401(self, client):
        response = client.get("/tmp", headers={})
        assert response.status_code == 401

    def test_valid_path_returns_200(self, client, auth, fs):
        fs.create_file("/tmp/files/file.txt")
        response = client.get("/tmp/files/", headers=auth)
        assert response.status_code == 200
        assert response.json == ["file.txt"]

    def test_permission_denied_returns_403(self, client, auth, fs):
        fs.create_dir("/tmp/files/root", perm_bits=000)
        response = client.get("/tmp/files/root/", headers=auth)
        data = response.json
        assert response.status_code == 403
        assert data["code"] == 403
        assert data["reason"] == "Forbidden"
        assert "Permission denied" in data["message"]

    def test_missing_path_returns_404(self, client, auth, fs):
        fs.create_dir("/tmp/files/")
        response = client.get("/tmp/files/missing/", headers=auth)
        data = response.json
        assert response.status_code == 404
        assert data["code"] == 404
        assert data["reason"] == "Not Found"
        assert "No such file or directory" in data["message"]

    def test_file_attachment_returns_200(self, client, auth, fs):
        fs.create_file("/tmp/files/file.txt")
        headers = {**auth, "accept": "application/octet-stream"}
        response = client.get("/tmp/files/file.txt", headers=headers)
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=file.txt"
        )
        assert response.headers["Content-Type"] == "text/plain; charset=utf-8"

    def test_directory_attachment_returns_200(self, client, auth, fs):
        fs.create_dir("/tmp/dirs/dir")
        headers = {**auth, "accept": "application/octet-stream"}
        response = client.get("/tmp/dirs/dir/", headers=headers)
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=dir.tar.gz"
        )
        assert response.headers["Content-Type"] == "application/gzip"

    def test_unsupported_accept_header_path_returns_400(self, client, auth):
        headers = {**auth, "accept": "text/html"}
        response = client.get("/tmp/files/", headers=headers)
        assert response.status_code == 400
        assert response.json == {
            "code": 400,
            "message": "unsupported 'accept' HTTP header",
            "reason": "Bad Request",
        }


class TestFilesystemPOST:
    def test_file_returns_201(self, client, auth, fs):
        fs.create_dir("/tmp/files/")
        response = client.post(
            "/tmp/files/",
            headers=auth,
            data={"files": (io.BytesIO(b"text"), "file.txt")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 201
        assert fs.exists("/tmp/files/file.txt") is True
        with open("/tmp/files/file.txt") as fd:
            assert fd.read() == "text"

    def test_missing_path_returns_400(self, client, auth, fs):
        fs.create_dir("/tmp/files/")
        response = client.post(
            "/tmp/files/missing/",
            headers=auth,
            data={"files": (None, "file.txt")},
            content_type="multipart/form-data",
        )
        data = response.json
        assert response.status_code == 400
        assert data["code"] == 400
        assert data["reason"] == "Bad Request"
        assert "No such file or directory" in data["message"]

    def test_missing_data_returns_400(self, client, auth, fs):
        fs.create_dir("/tmp/files/")
        response = client.post(
            "/tmp/files/",
            headers=auth,
            data={},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.json == {
            "code": 400,
            "message": "missing files",
            "reason": "Bad Request",
        }

    def test_create_existing_file_returns_400(self, client, auth, fs):
        fs.create_file("/tmp/files/file.txt")
        response = client.post(
            "/tmp/files/",
            headers=auth,
            data={"files": (None, "file.txt")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.json == {
            "code": 400,
            "message": "a file already exists in given path",
            "reason": "Bad Request",
        }

    def test_permission_denied_returns_403(self, client, auth, fs):
        fs.create_dir("/tmp/files/root", perm_bits=000)
        response = client.post(
            "/tmp/files/root/",
            headers=auth,
            data={"files": (io.BytesIO(b"text"), "file.txt")},
            content_type="multipart/form-data",
        )
        data = response.json
        assert response.status_code == 403
        assert data["code"] == 403
        assert data["reason"] == "Forbidden"
        assert "Permission denied" in data["message"]


class TestFilesystemPUT:
    def test_valid_file_returns_204(self, client, auth, fs):
        fs.create_file("/tmp/files/file.txt")
        response = client.put(
            "/tmp/files/",
            headers=auth,
            data={"files": (io.BytesIO(b"text"), "file.txt")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 204
        with open("/tmp/files/file.txt") as fd:
            assert fd.read() == "text"

    def test_missing_file_path_returns_400(self, client, auth, fs):
        fs.create_dir("/tmp/files/")
        response = client.put(
            "/tmp/files/",
            headers=auth,
            data={"files": (None, "file.txt")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.json == {
            "code": 400,
            "reason": "Bad Request",
            "message": "a file does not exist in given path",
        }

    def test_wrong_path_returns_400(self, client, auth, fs):
        fs.create_dir("/tmp/files/")
        response = client.put(
            "/tmp/files/file.txt",
            headers=auth,
            data={"files": (None, "file.txt")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.json == {
            "code": 400,
            "reason": "Bad Request",
            "message": "a file does not exist in given path",
        }

    def test_permission_denied_returns_403(self, client, auth, fs):
        fs.create_file("/tmp/files/root.txt", st_mode=0o000)
        response = client.put(
            "/tmp/files/",
            headers=auth,
            data={"files": (None, "root.txt")},
            content_type="multipart/form-data",
        )
        data = response.json
        assert response.status_code == 403
        assert data["code"] == 403
        assert data["reason"] == "Forbidden"
        assert "Permission denied" in data["message"]


class TestFilesystemDELETE:
    def test_valid_file_returns_204(self, client, auth, fs):
        fs.create_file("/tmp/files/file.txt")
        response = client.delete("/tmp/files/file.txt", headers=auth)
        assert response.status_code == 204
        assert fs.exists("/tmp/files/file.txt") is False

    def test_valid_dir_returns_204(self, client, auth, fs):
        fs.create_dir("/tmp/dirs/dir")
        response = client.delete("/tmp/dirs/dir/", headers=auth)
        assert response.status_code == 204
        assert fs.exists("/tmp/dirs/dir") is False

    def test_delete_missing_path_returns_404(self, client, auth, fs):
        fs.create_dir("/tmp/files/")
        response = client.delete("/tmp/files/file.txt", headers=auth)
        data = response.json
        assert response.status_code == 400
        assert data["code"] == 400
        assert data["reason"] == "Bad Request"
        assert "No such file or directory" in data["message"]

    def test_permission_denied_returns_403(self, client, auth, fs):
        fs.create_dir("/tmp/files/root", perm_bits=000)
        response = client.delete("/tmp/files/root", headers=auth)
        data = response.json
        assert response.status_code == 403
        assert data["code"] == 403
        assert data["reason"] == "Forbidden"
        assert "Permission denied" in data["message"]
