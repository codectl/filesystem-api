import io
import json


class TestFileManagerActions:
    def test_read_action(self, client, fs):
        fs.create_file("/tmp/files/file1.txt")
        fs.create_file("/tmp/files/.file2.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": "/tmp/files",
                "showHiddenItems": True,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["cwd"]["name"] == "files"
        assert data["cwd"]["path"] == "/tmp/files"
        assert len(data["files"]) == 2

    def test_create_action(self, client, fs):
        fs.create_dir("/tmp/dirs")
        response = client.post(
            "/file-manager/actions",
            json={"action": "create", "path": "/tmp/dirs", "name": "dir", "data": []},
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "dir"
        assert data["files"][0]["path"] == "/tmp/dirs/dir"
        assert data["files"][0]["isFile"] is False
        assert data["files"][0]["hasChild"] is False
        assert fs.exists("/tmp/dirs/dir")

    def test_delete_action(self, client, fs):
        base = "/tmp/files"
        fs.create_file(f"{base}/file1.txt")
        fs.create_file(f"{base}/file2.txt")
        fs.create_file(f"{base}/file3.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "delete",
                "path": base,
                "names": ["file1.txt", "file2.txt"],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 2
        assert any(file["path"] == f"{base}/file1.txt" for file in data["files"])
        assert any(file["path"] == f"{base}/file2.txt" for file in data["files"])
        assert fs.exists(f"{base}/file1.txt") is False
        assert fs.exists(f"{base}/file2.txt") is False
        assert fs.exists(f"{base}/file3.txt") is True

    def test_rename_action(self, client, fs):
        fs.create_file("/tmp/files/file1.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "rename",
                "path": "/tmp/files",
                "name": "file1.txt",
                "newName": "file2.txt",
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "file2.txt"
        assert data["files"][0]["path"] == "/tmp/files/file2.txt"
        assert data["files"][0]["isFile"] is True
        assert fs.exists("/tmp/files/file1.txt") is False
        assert fs.exists("/tmp/files/file2.txt") is True

    def test_rename_existing_name_action(self, client, fs):
        fs.create_file("/tmp/files/file1.txt")
        fs.create_file("/tmp/files/file2.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "rename",
                "path": "/tmp/files",
                "name": "file1.txt",
                "newName": "file2.txt",
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["error"]["code"] == 400
        assert "destination already exists" in data["error"]["message"]

    def test_search_action(self, client, fs):
        base = "/tmp/files"
        fs.create_file(f"{base}/file1.txt")
        fs.create_file(f"{base}/.file2.txt")
        fs.create_file(f"{base}/test.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "search",
                "path": base,
                "showHiddenItems": True,
                "caseSensitive": True,
                "searchString": "file",
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 2
        assert any(file["path"] == f"{base}/file1.txt" for file in data["files"])
        assert any(file["path"] == f"{base}/.file2.txt" for file in data["files"])

    def test_file_details_action(self, client, fs):
        fs.create_file("/tmp/files/file.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "details",
                "path": "/tmp/files",
                "names": ["file.txt"],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["details"]["name"] == "file.txt"
        assert data["details"]["location"] == "/tmp/files/file.txt"
        assert data["details"]["isFile"] is True
        assert data["details"]["multipleFiles"] is False
        assert data["details"]["size"] == "0 B"

    def test_dir_details_action(self, client, fs):
        fs.create_dir("/tmp/dirs/dir")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "details",
                "path": "/tmp/dirs",
                "names": ["dir"],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["details"]["name"] == "dir"
        assert data["details"]["location"] == "/tmp/dirs/dir"
        assert data["details"]["isFile"] is False
        assert data["details"]["multipleFiles"] is False
        assert data["details"]["size"] == "0 B"

    def test_multiple_files_details_action(self, client, fs):
        fs.create_dir("/tmp/files/dir")
        fs.create_file("/tmp/files/file.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "details",
                "path": "/tmp/files",
                "names": ["dir", "file.txt"],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["details"]["name"] == "dir, file.txt"
        assert data["details"]["location"] == "All in /tmp/files"
        assert data["details"]["isFile"] is False
        assert data["details"]["multipleFiles"] is True
        assert data["details"]["size"] == "0 B"

    def test_copy_action(self, client, fs):
        fs.create_file("/tmp/files/src/file1.txt")
        fs.create_file("/tmp/files/src/file2.txt")
        fs.create_file("/tmp/files/dst/file2.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "copy",
                "path": "/tmp/files/src",
                "names": ["file1.txt", "file2.txt"],
                "renameFiles": [],
                "targetPath": "/tmp/files/dst",
                "targetData": None,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 2
        assert any(file["name"] == "file1.txt" for file in data["files"]) is True
        assert any(file["name"] == "file2 (1).txt" for file in data["files"]) is True
        assert fs.exists("/tmp/files/src/file1.txt") is True
        assert fs.exists("/tmp/files/dst/file2.txt") is True
        assert fs.exists("/tmp/files/dst/file2 (1).txt") is True

    def test_move_action(self, client, fs):
        fs.create_file("/tmp/files/src/file1.txt")
        fs.create_file("/tmp/files/src/file2.txt")
        fs.create_file("/tmp/files/dst/file2.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "move",
                "path": "/tmp/files/src",
                "names": ["file1.txt", "file2.txt"],
                "renameFiles": [],
                "targetPath": "/tmp/files/dst",
                "targetData": None,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "file1.txt"
        assert data["files"][0]["path"] == "/tmp/files/dst/file1.txt"
        assert data["error"]["code"] == 400
        assert data["error"]["message"] == "File Already Exists"
        assert data["error"]["fileExists"] == ["file2.txt"]
        assert fs.exists("/tmp/files/src/file1.txt") is False
        assert fs.exists("/tmp/files/src/file2.txt") is True
        assert fs.exists("/tmp/files/dst/file1.txt") is True

    def test_override_move_action(self, client, fs):
        fs.create_file("/tmp/files/src/file.txt")
        fs.create_file("/tmp/files/dst/file.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "move",
                "path": "/tmp/files/src",
                "names": ["file.txt"],
                "renameFiles": ["file.txt"],
                "targetPath": "/tmp/files/dst",
                "targetData": None,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "file (1).txt"
        assert data["files"][0]["path"] == "/tmp/files/dst/file (1).txt"
        assert fs.exists("/tmp/files/src/file.txt") is False
        assert fs.exists("/tmp/files/dst/file.txt") is True
        assert fs.exists("/tmp/files/dst/file (1).txt") is True

    def test_missing_path_sends_error(self, client, fs):
        fs.create_dir("/tmp/files")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": "/tmp/files/file.txt",
                "showHiddenItems": True,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["error"]["code"] == 404
        assert data["error"]["message"] == "File Not Found"

    def test_permission_denied_sends_error(self, client, fs):
        fs.create_file("/tmp/files/root.txt", st_mode=0o000)
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": "/tmp/files/root.txt",
                "showHiddenItems": True,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["error"]["code"] == 403
        assert data["error"]["message"] == "Permission Denied"


class TestFileManagerDownload:
    def test_single_file_download_action(self, client, fs):
        fs.create_file("/tmp/files/file.txt")
        response = client.post(
            "/file-manager/download",
            data={
                "downloadInput": json.dumps(
                    {
                        "action": "download",
                        "path": "/tmp/files",
                        "names": ["file.txt"],
                        "data": [],
                    }
                )
            },
        )
        headers = response.headers
        assert response.status_code == 200
        assert headers["Content-Disposition"] == "attachment; filename=file.txt"
        assert headers["Content-Type"] == "text/plain; charset=utf-8"

    def test_multiple_files_download_action(self, client, fs):
        fs.create_file("/tmp/files/file1.txt")
        fs.create_file("/tmp/files/file2.txt")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = client.post(
            "/file-manager/download",
            headers=headers,
            data={
                "downloadInput": json.dumps(
                    {
                        "action": "download",
                        "path": "/tmp/files",
                        "names": ["file1.txt", "file2.txt"],
                        "data": [],
                    }
                )
            },
        )
        headers = response.headers
        assert response.status_code == 200
        assert headers["Content-Disposition"] == "attachment; filename=files.tar.gz"
        assert headers["Content-Type"] == "application/gzip"

    def test_missing_path_raises_404(self, client, fs):
        fs.create_dir("/tmp/files")
        response = client.post(
            "/file-manager/download",
            data={
                "downloadInput": json.dumps(
                    {
                        "action": "download",
                        "path": "/tmp/files",
                        "names": ["file.txt"],
                        "data": [],
                    }
                )
            },
        )
        assert response.status_code == 404
        assert response.json == {"code": 404, "reason": "Not Found", "message": ""}


class TestFileManagerUpload:
    def test_file_upload_action(self, client, fs):
        fs.create_dir("/tmp/files")
        response = client.post(
            "/file-manager/upload",
            data={
                "action": "save",
                "path": "/tmp/files",
                "cancel-uploading": False,
                "uploadFiles": (io.BytesIO(b"text"), "file.txt"),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert fs.exists("/tmp/files/file.txt") is True
        with open("/tmp/files/file.txt") as fd:
            assert fd.read() == "text"

    def test_missing_path_raises_404(self, client, fs):
        fs.create_dir("/tmp/dirs")
        response = client.post(
            "/file-manager/upload",
            data={
                "action": "save",
                "path": "/tmp/dirs/dir",
                "cancel-uploading": False,
                "uploadFiles": (None, "file.txt"),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 404
        assert response.json == {"code": 404, "reason": "Not Found", "message": ""}


class TestFileManagerImages:
    def test_get_image(self, client, fs):
        fs.create_file("/tmp/files/img.jpeg")
        response = client.get(
            "/file-manager/images",
            query_string={"path": "/tmp/files/img.jpeg"},
        )
        headers = response.headers
        assert response.status_code == 200
        assert headers["Content-Disposition"] == "inline; filename=img.jpeg"
        assert headers["Content-Type"] == "image/jpeg"

    def test_missing_path_raises_404(self, client, fs):
        fs.create_dir("/tmp/files")
        response = client.get(
            "/file-manager/images",
            query_string={"path": "/tmp/files/img.jpeg"},
        )
        assert response.status_code == 404
        assert response.json == {"code": 404, "reason": "Not Found", "message": ""}
