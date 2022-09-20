import io
from base64 import b64encode

import pytest

from src.services.auth import AuthSvc
from src.services.filemgr import FileManagerSvc


@pytest.fixture(scope="class")
def svc():
    return FileManagerSvc(username="test")


@pytest.fixture()
def auth(mocker):
    mocker.patch.object(AuthSvc, "authenticate", return_value=True)
    return {"Authorization": f"Basic {b64encode(b'user:pass').decode()}"}


class TestFilesystemGET:
    def test_unauthorized_request_throws_401(self, client, file):
        path = file.as_posix()
        response = client.get(path, headers={})
        assert response.status_code == 401

    def test_valid_path_returns_200(self, client, auth, file):
        path = file.parent.as_posix()
        response = client.get(path, headers=auth)
        assert response.status_code == 200
        assert response.json == ["file.txt"]

    def test_permission_denied_returns_403(self, client, auth, filedir):
        path = filedir.as_posix()
        filedir.chmod(0o000)
        response = client.get(path, headers=auth)
        filedir.chmod(0o755)
        data = response.json
        assert response.status_code == 403
        assert data["code"] == 403
        assert data["reason"] == "Forbidden"
        assert "Permission denied" in data["message"]

    def test_missing_path_returns_404(self, client, auth, tmp_path):
        path = (tmp_path / "dir").as_posix()
        response = client.get(path, headers=auth)
        data = response.json
        assert response.status_code == 404
        assert data["code"] == 404
        assert data["reason"] == "Not Found"
        assert "No such file or directory" in data["message"]

    def test_file_attachment_returns_200(self, client, auth, file):
        path = file.as_posix()
        headers = {**auth, "accept": "application/octet-stream"}
        response = client.get(path, headers=headers)
        headers = response.headers
        assert response.status_code == 200
        assert headers["Content-Disposition"] == "attachment; filename=file.txt"
        assert headers["Content-Type"] == "text/plain; charset=utf-8"

    def test_directory_attachment_returns_200(self, client, auth, filedir):
        path = filedir.as_posix()
        headers = {**auth, "accept": "application/octet-stream"}
        response = client.get(path, headers=headers)
        headers = response.headers
        assert response.status_code == 200
        assert headers["Content-Disposition"] == "attachment; filename=dir.tar.gz"
        assert headers["Content-Type"] == "application/gzip"

    def test_unsupported_accept_header_path_returns_400(self, client, auth, tmp_path):
        path = tmp_path.as_posix()
        headers = {**auth, "accept": "text/html"}
        response = client.get(path, headers=headers)
        assert response.status_code == 400
        assert response.json == {
            "code": 400,
            "message": "unsupported 'accept' HTTP header",
            "reason": "Bad Request",
        }


class TestFilesystemPOST:
    def test_create_file_returns_201(self, client, auth, file, filedir):
        path = filedir.as_posix()
        response = client.post(
            path,
            headers=auth,
            data={"files": (io.BytesIO(b"new content"), file.name)},
            content_type="multipart/form-data",
        )
        assert response.status_code == 201
        assert file.exists() is True

    def test_missing_path_returns_400(self, client, auth, file, tmp_path):
        path = (tmp_path / "xyz").as_posix()
        response = client.post(
            path,
            headers=auth,
            data={"files": (None, file.name)},
            content_type="multipart/form-data",
        )
        data = response.json
        assert response.status_code == 400
        assert data["code"] == 400
        assert data["reason"] == "Bad Request"
        assert "No such file or directory" in data["message"]

    def test_missing_data_returns_400(self, client, auth, tmp_path):
        path = tmp_path.as_posix()
        response = client.post(
            path,
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

    def test_create_existing_file_returns_400(self, client, auth, file):
        path = file.parent.as_posix()
        response = client.post(
            path,
            headers=auth,
            data={"files": (None, file.name)},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.json == {
            "code": 400,
            "message": "a file already exists in given path",
            "reason": "Bad Request",
        }

    def test_permission_denied_returns_403(self, client, auth, filedir, file):
        path = filedir.as_posix()
        filedir.chmod(mode=0o000)
        response = client.post(
            path,
            headers=auth,
            data={"files": (io.BytesIO(b"text"), file.name)},
            content_type="multipart/form-data",
        )
        filedir.chmod(mode=0o444)
        data = response.json
        assert response.status_code == 403
        assert data["code"] == 403
        assert data["reason"] == "Forbidden"
        assert "Permission denied" in data["message"]


class TestFilesystemPUT:
    def test_update_file_returns_204(self, client, auth, file):
        path = file.parent.as_posix()
        response = client.put(
            path,
            headers=auth,
            data={"files": (io.BytesIO(b"new content"), file.name)},
            content_type="multipart/form-data",
        )
        assert response.status_code == 204

    def test_update_missing_file_returns_400(self, client, auth, file, filedir):
        path = filedir.as_posix()
        response = client.put(
            path,
            headers=auth,
            data={"files": (None, file.name)},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.json == {
            "code": 400,
            "reason": "Bad Request",
            "message": "a file does not exist in given path",
        }

    def test_wrong_path_returns_400(self, client, auth, file, tmp_path):
        path = (tmp_path / "xyz").as_posix()
        response = client.put(
            path,
            headers=auth,
            data={"files": (None, file.name)},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.json == {
            "code": 400,
            "reason": "Bad Request",
            "message": "a file does not exist in given path",
        }

    def test_permission_denied_returns_403(self, client, auth, filedir, file):
        path = filedir.as_posix()
        filedir.chmod(mode=0o000)
        response = client.put(
            path,
            headers=auth,
            data={"files": (None, file.name)},
            content_type="multipart/form-data",
        )
        filedir.chmod(mode=0o444)
        data = response.json
        assert response.status_code == 403
        assert data["code"] == 403
        assert data["reason"] == "Forbidden"
        assert "Permission denied" in data["message"]


class TestFilesystemDELETE:
    def test_delete_file_returns_204(self, client, auth, file):
        path = file.as_posix()
        response = client.delete(path, headers=auth)
        assert response.status_code == 204
        assert file.exists() is False

    def test_delete_dir_returns_204(self, client, auth, tmp_path):
        subdir = tmp_path / "dir"
        subdir.mkdir()
        path = subdir.as_posix()
        response = client.delete(path, headers=auth)
        assert response.status_code == 204
        assert subdir.exists() is False

    def test_delete_nonempty_dir_returns_400(self, client, auth, file):
        path = file.parent.as_posix()
        response = client.delete(path, headers=auth)
        data = response.json
        assert response.status_code == 400
        assert data["code"] == 400
        assert data["reason"] == "Bad Request"
        assert "Directory not empty" in data["message"]

    def test_delete_missing_file_returns_400(self, client, auth, tmp_path):
        path = (tmp_path / "xyz").as_posix()
        response = client.delete(path, headers=auth)
        data = response.json
        assert response.status_code == 400
        assert data["code"] == 400
        assert data["reason"] == "Bad Request"
        assert "No such file or directory" in data["message"]

    def test_permission_denied_returns_403(self, client, auth, filedir):
        path = (filedir / "file.txt").as_posix()
        filedir.chmod(mode=0o000)
        response = client.delete(path, headers=auth)
        filedir.chmod(mode=0o755)
        data = response.json
        assert response.status_code == 403
        assert data["code"] == 403
        assert data["reason"] == "Forbidden"
        assert "Permission denied" in data["message"]
