import json


class TestFileManagerActions:
    def test_read_action(self, client, fs):
        fs.create_file("/tmp/file1.txt")
        fs.create_file("/tmp/.file2.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": "/tmp",
                "showHiddenItems": True,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["cwd"]["name"] == "tmp"
        assert data["cwd"]["path"] == "/tmp"
        assert len(data["files"]) == 2

    def test_create_action(self, client, fs):
        fs.create_dir("/tmp")
        response = client.post(
            "/file-manager/actions",
            json={"action": "create", "path": "/tmp", "name": "dir", "data": []},
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "dir"
        assert data["files"][0]["path"] == "/tmp/dir"
        assert data["files"][0]["isFile"] is False
        assert data["files"][0]["hasChild"] is False
        assert fs.exists("/tmp/dir")

    def test_delete_action(self, client, fs):
        fs.create_file("/tmp/file1.txt")
        fs.create_file("/tmp/file2.txt")
        fs.create_file("/tmp/file3.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "delete",
                "path": "/tmp",
                "names": ["file1.txt", "file2.txt"],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 2
        assert any(file["path"] == "/tmp/file1.txt" for file in data["files"]) is True
        assert any(file["path"] == "/tmp/file2.txt" for file in data["files"]) is True
        assert fs.exists("/tmp/file1.txt") is False
        assert fs.exists("/tmp/file2.txt") is False
        assert fs.exists("/tmp/file3.txt") is True

    def test_rename_action(self, client, fs):
        fs.create_file("/tmp/file1.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "rename",
                "path": "/tmp",
                "name": "file1.txt",
                "newName": "file2.txt",
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "file2.txt"
        assert data["files"][0]["path"] == "/tmp/file2.txt"
        assert data["files"][0]["isFile"] is True
        assert fs.exists("/tmp/file1.txt") is False
        assert fs.exists("/tmp/file2.txt") is True

    def test_rename_existing_name_action(self, client, fs):
        fs.create_file("/tmp/file1.txt")
        fs.create_file("/tmp/file2.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "rename",
                "path": "/tmp",
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
        fs.create_file("/tmp/file1.txt")
        fs.create_file("/tmp/.file2.txt")
        fs.create_file("/tmp/test.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "search",
                "path": "/tmp",
                "showHiddenItems": True,
                "caseSensitive": True,
                "searchString": "file",
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 2
        assert any(file["path"] == "/tmp/file1.txt" for file in data["files"]) is True
        assert any(file["path"] == "/tmp/.file2.txt" for file in data["files"]) is True

    def test_file_details_action(self, client, fs):
        fs.create_file("/tmp/file.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "details",
                "path": "/tmp",
                "names": ["file.txt"],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["details"]["name"] == "file.txt"
        assert data["details"]["location"] == "/tmp/file.txt"
        assert data["details"]["isFile"] is True
        assert data["details"]["multipleFiles"] is False
        assert data["details"]["size"] == "0 B"

    def test_dir_details_action(self, client, fs):
        fs.create_dir("/tmp/dir")
        response = client.post(
            "/file-manager/actions",
            json={"action": "details", "path": "/tmp", "names": ["dir"], "data": []},
        )
        data = response.json
        assert response.status_code == 200
        assert data["details"]["name"] == "dir"
        assert data["details"]["location"] == "/tmp/dir"
        assert data["details"]["isFile"] is False
        assert data["details"]["multipleFiles"] is False
        assert data["details"]["size"] == "0 B"

    def test_multiple_files_details_action(self, client, fs):
        fs.create_dir("/tmp/dir")
        fs.create_dir("/tmp/file.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "details",
                "path": "/tmp",
                "names": ["dir", "file.txt"],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["details"]["name"] == "dir, file.txt"
        assert data["details"]["location"] == "All in /tmp"
        assert data["details"]["isFile"] is False
        assert data["details"]["multipleFiles"] is True
        assert data["details"]["size"] == "0 B"

    def test_copy_action(self, client, fs):
        fs.create_file("/tmp/src/file1.txt")
        fs.create_file("/tmp/src/file2.txt")
        fs.create_file("/tmp/dst/file2.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "copy",
                "path": "/tmp/src",
                "names": ["file1.txt", "file2.txt"],
                "renameFiles": [],
                "targetPath": "/tmp/dst",
                "targetData": None,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 2
        assert any(file["name"] == "file1.txt" for file in data["files"]) is True
        assert any(file["name"] == "file2 (1).txt" for file in data["files"]) is True
        assert fs.exists("/tmp/src/file1.txt") is True
        assert fs.exists("/tmp/dst/file2.txt") is True
        assert fs.exists("/tmp/dst/file2 (1).txt") is True

    def test_move_action(self, client, fs):
        fs.create_file("/tmp/src/file1.txt")
        fs.create_file("/tmp/src/file2.txt")
        fs.create_file("/tmp/dst/file2.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "move",
                "path": "/tmp/src",
                "names": ["file1.txt", "file2.txt"],
                "renameFiles": [],
                "targetPath": "/tmp/dst",
                "targetData": None,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "file1.txt"
        assert data["files"][0]["path"] == "/tmp/dst/file1.txt"
        assert data["error"]["code"] == 400
        assert data["error"]["message"] == "File Already Exists"
        assert data["error"]["fileExists"] == ["file2.txt"]
        assert fs.exists("/tmp/src/file1.txt") is False
        assert fs.exists("/tmp/src/file2.txt") is True
        assert fs.exists("/tmp/dst/file1.txt") is True

    def test_override_move_action(self, client, fs):
        fs.create_file("/tmp/src/file.txt")
        fs.create_file("/tmp/dst/file.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "move",
                "path": "/tmp/src",
                "names": ["file.txt"],
                "renameFiles": ["file.txt"],
                "targetPath": "/tmp/dst",
                "targetData": None,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "file (1).txt"
        assert data["files"][0]["path"] == "/tmp/dst/file (1).txt"
        assert fs.exists("/tmp/src/file.txt") is False
        assert fs.exists("/tmp/dst/file.txt") is True
        assert fs.exists("/tmp/dst/file (1).txt") is True

    def test_missing_path_sends_error(self, client, fs):
        fs.create_dir("/tmp")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": "/tmp/file.txt",
                "showHiddenItems": True,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["error"]["code"] == 404
        assert data["error"]["message"] == "File Not Found"

    def test_permission_denied_sends_error(self, client, fs):
        fs.create_file("/tmp/root.txt", st_mode=0o000)
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": "/tmp/root.txt",
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
        fs.create_file("/tmp/file.txt")
        response = client.post(
            "/file-manager/download",
            data={
                "downloadInput": json.dumps(
                    {
                        "action": "download",
                        "path": "/tmp",
                        "names": ["file.txt"],
                        "data": [],
                    }
                )
            },
        )
        headers = response.headers
        assert response.status_code == 200
        assert headers["Content-Disposition"] == f"attachment; filename=file.txt"
        assert headers["Content-Type"] == "text/plain; charset=utf-8"

    def test_multiple_files_download_action(self, client, fs):
        fs.create_file("/tmp/file1.txt")
        fs.create_file("/tmp/file2.txt")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = client.post(
            "/file-manager/download",
            headers=headers,
            data={
                "downloadInput": json.dumps(
                    {
                        "action": "download",
                        "path": "/tmp",
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

    def test_missing_path_sends_error(self, client, fs):
        fs.create_dir("/tmp")
        response = client.post(
            "/file-manager/download",
            data={
                "downloadInput": json.dumps(
                    {
                        "action": "download",
                        "path": "/tmp",
                        "names": ["file.txt"],
                        "data": [],
                    }
                )
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["error"]["code"] == 404
        assert data["error"]["message"] == "File Not Found"
