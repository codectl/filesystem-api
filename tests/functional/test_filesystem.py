# import io
# import subprocess
# from base64 import b64encode
#
# import pytest
#
# from src.services.auth import AuthSvc
#
#
# @pytest.fixture()
# def auth(mocker):
#     mocker.patch.object(AuthSvc, "authenticate", return_value=True)
#     return {"Authorization": f"Basic {b64encode(b'user:pass').decode()}"}
#
#
# class TestFilesystemGET:
#     def test_unauthorized_request_throws_401(self, client):
#         response = client.get("/filesystem/tmp/", headers={})
#         assert response.status_code == 401
#
#     def test_unsupported_value_throws_400(self, client, auth):
#         response = client.get("/filesystem/unsupported/", headers=auth)
#         assert response.status_code == 400
#
#     def test_valid_path_returns_200(self, client, auth, mocker):
#         mocker.patch("src.utils.shell", return_value="file.txt")
#         response = client.get("/filesystem/tmp/", headers=auth)
#         assert response.status_code == 200
#         assert response.json == ["file.txt"]
#
#     def test_error_path_returns_400(self, client, auth, mocker):
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr="err")
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.get("/filesystem/tmp/invalid/", headers=auth)
#         assert response.status_code == 400
#         assert response.json == {"code": 400, "message": "err", "reason": "Bad Request"}
#
#     def test_permission_denied_returns_403(self, client, auth, mocker):
#         stderr = "/tmp/root/: Permission denied"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.get("/filesystem/tmp/root/", headers=auth)
#         assert response.status_code == 403
#         assert response.json == {
#             "code": 403,
#             "message": "permission denied",
#             "reason": "Forbidden",
#         }
#
#     def test_missing_path_returns_404(self, client, auth, mocker):
#         stderr = "/tmp/missing/: No such file or directory"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.get("/filesystem/tmp/missing/", headers=auth)
#         assert response.status_code == 404
#         assert response.json == {
#             "code": 404,
#             "message": "no such file or directory",
#             "reason": "Not Found",
#         }
#
#     def test_file_attachment_returns_200(self, client, auth, mocker):
#         mocker.patch("src.utils.shell", side_effect=["file.txt", b""])
#         mocker.patch("src.utils.isfile", return_value=True)
#         headers = {**auth, "accept": "application/octet-stream"}
#         response = client.get("/filesystem/tmp/file.txt", headers=headers)
#         assert response.status_code == 200
#         assert (
#             response.headers["Content-Disposition"] == "attachment; filename=file.txt"
#         )
#         assert response.headers["Content-Type"] == "text/plain; charset=utf-8"
#
#     def test_directory_attachment_returns_200(self, client, auth, mocker):
#         mocker.patch("src.utils.shell", side_effect=["dir/", b""])
#         mocker.patch("src.utils.isdir", return_value=True)
#         headers = {**auth, "accept": "application/octet-stream"}
#         response = client.get("/filesystem/tmp/dir/", headers=headers)
#         assert response.status_code == 200
#         assert (
#             response.headers["Content-Disposition"] == "attachment; filename=dir.tar.gz"
#         )
#         assert response.headers["Content-Type"] == "application/x-tar"
#
#     def test_unsupported_accept_header_path_returns_400(self, client, auth):
#         headers = {**auth, "accept": "text/html"}
#         response = client.get("/filesystem/tmp/", headers=headers)
#         assert response.status_code == 400
#         assert response.json == {
#             "code": 400,
#             "message": "unsupported 'accept' HTTP header",
#             "reason": "Bad Request",
#         }
#
#
# class TestFilesystemPOST:
#     def test_valid_file_returns_201(self, client, auth, mocker):
#         mocker.patch("src.utils.shell")
#         response = client.post(
#             "/filesystem/tmp/",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 201
#
#     def test_path_not_a_directory_returns_400(self, client, auth, mocker):
#         stderr = "/tmp/file.txt: Not a directory"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.post(
#             "/filesystem/tmp/file.txt",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 400
#
#     def test_create_existing_file_returns_400(self, client, auth, mocker):
#         mocker.patch("src.utils.shell", return_value="file.txt")
#         response = client.post(
#             "/filesystem/tmp/file.txt",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 400
#
#     def test_permission_denied_returns_403(self, client, auth, mocker):
#         stderr = "/tmp/root/: Permission denied"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.post(
#             "/filesystem/tmp/root/",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 403
#         assert response.json == {
#             "code": 403,
#             "message": "permission denied",
#             "reason": "Forbidden",
#         }
#
#     def test_missing_path_returns_404(self, client, auth, mocker):
#         stderr = "/tmp/missing/: No such file or directory"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.post(
#             "/filesystem/tmp/missing/",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 404
#         assert response.json == {
#             "code": 404,
#             "message": "no such file or directory",
#             "reason": "Not Found",
#         }
#
#
# class TestFilesystemPUT:
#     def test_valid_file_returns_204(self, client, auth, mocker):
#         mocker.patch("src.utils.shell", return_value="file.txt")
#         response = client.put(
#             "/filesystem/tmp/file.txt",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 204
#
#     def test_path_not_a_directory_returns_400(self, client, auth, mocker):
#         stderr = "/tmp/file.txt: Not a directory"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.put(
#             "/filesystem/tmp/file.txt",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 400
#
#     def test_permission_denied_returns_403(self, client, auth, mocker):
#         stderr = "/tmp/root/: Permission denied"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.put(
#             "/filesystem/tmp/root/",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 403
#         assert response.json == {
#             "code": 403,
#             "message": "permission denied",
#             "reason": "Forbidden",
#         }
#
#     def test_missing_path_returns_404(self, client, auth, mocker):
#         stderr = "/tmp/missing/: No such file or directory"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.put(
#             "/filesystem/tmp/missing/",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 404
#         assert response.json == {
#             "code": 404,
#             "message": "no such file or directory",
#             "reason": "Not Found",
#         }
#
#     def test_update_missing_file_returns_404(self, client, auth, mocker):
#         mocker.patch("src.utils.shell", return_value="")
#         response = client.put(
#             "/filesystem/tmp/",
#             headers=auth,
#             data={"files": (io.BytesIO(b"text"), "file.txt")},
#             content_type="multipart/form-data",
#         )
#         assert response.status_code == 404
#         assert response.json == {
#             "code": 404,
#             "message": "file does not exist",
#             "reason": "Not Found",
#         }
#
#
# class TestFilesystemDELETE:
#     def test_valid_file_returns_204(self, client, auth, mocker):
#         mocker.patch("src.utils.shell")
#         response = client.delete("/filesystem/tmp/file.txt", headers=auth)
#         assert response.status_code == 204
#
#     def test_path_is_a_directory_returns_400(self, client, auth, mocker):
#         stderr = "/tmp/dir/: is a directory"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.delete("/filesystem/tmp/dir/", headers=auth)
#         assert response.status_code == 400
#
#     def test_permission_denied_returns_403(self, client, auth, mocker):
#         stderr = "/tmp/root/: Permission denied"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.delete("/filesystem/tmp/root/", headers=auth)
#         assert response.status_code == 403
#         assert response.json == {
#             "code": 403,
#             "message": "permission denied",
#             "reason": "Forbidden",
#         }
#
#     def test_delete_missing_file_returns_404(self, client, auth, mocker):
#         stderr = "/tmp/file.txt: No such file or directory"
#         err = subprocess.CalledProcessError(cmd="", returncode=1, stderr=stderr)
#         mocker.patch("src.utils.shell", side_effect=err)
#         response = client.delete("/filesystem/tmp/file.txt", headers=auth)
#         assert response.status_code == 404
#         assert response.json == {
#             "code": 404,
#             "message": "no such file or directory",
#             "reason": "Not Found",
#         }
