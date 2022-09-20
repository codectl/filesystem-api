import io
import json


class TestFileManagerActions:
    def test_read_action(self, client, tmp_path):
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        (tmp_path / ".file3.txt").touch()
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": tmp_path.as_posix(),
                "showHiddenItems": True,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["cwd"]["name"] == tmp_path.name
        assert data["cwd"]["path"] == tmp_path.as_posix()
        assert len(data["files"]) == 3

    def test_create_action(self, client, tmp_path):
        dirs = tmp_path / "dirs"
        dirs.mkdir()
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "create",
                "path": dirs.as_posix(),
                "name": "dir",
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == (dirs / "dir").name
        assert data["files"][0]["path"] == (dirs / "dir").as_posix()
        assert data["files"][0]["isFile"] is False
        assert data["files"][0]["hasChild"] is False
        assert (dirs / "dir").exists() is True

    def test_delete_action(self, client, tmp_path):
        path = tmp_path.as_posix()
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        (tmp_path / "file3.txt").touch()
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "delete",
                "path": path,
                "names": ["file1.txt", "file2.txt"],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 2
        assert any(file["path"] == f"{path}/file1.txt" for file in data["files"])
        assert any(file["path"] == f"{path}/file2.txt" for file in data["files"])
        assert (tmp_path / "file1.txt").exists() is False
        assert (tmp_path / "file2.txt").exists() is False
        assert (tmp_path / "file3.txt").exists() is True

    def test_rename_action(self, client, file):
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "rename",
                "path": file.parent.as_posix(),
                "name": file.name,
                "newName": "file2.txt",
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "file2.txt"
        assert data["files"][0]["path"] == (file.parent / "file2.txt").as_posix()
        assert data["files"][0]["isFile"] is True
        assert (file.parent / "file1.txt").exists() is False
        assert (file.parent / "file2.txt").exists() is True

    def test_rename_existing_name_action(self, client, tmp_path):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.touch()
        file2.touch()
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "rename",
                "path": tmp_path.as_posix(),
                "name": file1.name,
                "newName": file2.name,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["error"]["code"] == 400
        assert "destination already exists" in data["error"]["message"]

    def test_search_action(self, client, tmp_path):
        path = tmp_path.as_posix()
        (tmp_path / "file1.txt").touch()
        (tmp_path / ".file2.txt").touch()
        (tmp_path / "foo.txt").touch()
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "search",
                "path": path,
                "showHiddenItems": True,
                "caseSensitive": True,
                "searchString": "file",
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 2
        assert any(file["path"] == f"{path}/file1.txt" for file in data["files"])
        assert any(file["path"] == f"{path}/.file2.txt" for file in data["files"])

    def test_file_details_action(self, client, file):
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "details",
                "path": file.parent.as_posix(),
                "names": [file.name],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["details"]["name"] == file.name
        assert data["details"]["location"] == file.as_posix()
        assert data["details"]["isFile"] is True
        assert data["details"]["multipleFiles"] is False
        assert data["details"]["size"] == f"{file.stat().st_size} B"

    def test_dir_details_action(self, client, filedir):
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "details",
                "path": filedir.parent.as_posix(),
                "names": [filedir.name],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["details"]["name"] == filedir.name
        assert data["details"]["location"] == filedir.as_posix()
        assert data["details"]["isFile"] is False
        assert data["details"]["multipleFiles"] is False
        assert data["details"]["size"] == f"{filedir.stat().st_size} B"

    def test_multiple_files_details_action(self, client, tmp_path):
        file = tmp_path / "file.txt"
        filedir = tmp_path / "dir"
        file.touch()
        filedir.mkdir()
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "details",
                "path": tmp_path.as_posix(),
                "names": [filedir.name, file.name],
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["details"]["name"] == f"{filedir.name}, {file.name}"
        assert data["details"]["location"] == f"All in {tmp_path.as_posix()}"
        assert data["details"]["isFile"] is False
        assert data["details"]["multipleFiles"] is True
        assert data["details"]["size"] == f"{filedir.stat().st_size} B"

    def test_copy_action(self, client, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        (tmp_path / src / "file1.txt").touch()
        (tmp_path / src / "file2.txt").touch()
        (tmp_path / dst / "file2.txt").touch()
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "copy",
                "path": src.as_posix(),
                "names": ["file1.txt", "file2.txt"],
                "renameFiles": [],
                "targetPath": dst.as_posix(),
                "targetData": None,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 2
        assert any(file["name"] == "file1.txt" for file in data["files"]) is True
        assert any(file["name"] == "file2 (1).txt" for file in data["files"]) is True
        assert (dst / "file1.txt").exists() is True
        assert (dst / "file2.txt").exists() is True
        assert (dst / "file2 (1).txt").exists() is True

    def test_move_action(self, client, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        (tmp_path / src / "file1.txt").touch()
        (tmp_path / src / "file2.txt").touch()
        (tmp_path / dst / "file2.txt").touch()
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "move",
                "path": src.as_posix(),
                "names": ["file1.txt", "file2.txt"],
                "renameFiles": [],
                "targetPath": dst.as_posix(),
                "targetData": None,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "file1.txt"
        assert data["files"][0]["path"] == (dst / "file1.txt").as_posix()
        assert data["error"]["code"] == 400
        assert data["error"]["message"] == "File Already Exists"
        assert data["error"]["fileExists"] == ["file2.txt"]
        assert (src / "file1.txt").exists() is False
        assert (src / "file2.txt").exists() is True
        assert (dst / "file1.txt").exists() is True

    def test_override_move_action(self, client, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        dst.mkdir()
        (tmp_path / src / "file.txt").touch()
        (tmp_path / dst / "file.txt").touch()
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "move",
                "path": src.as_posix(),
                "names": ["file.txt"],
                "renameFiles": ["file.txt"],
                "targetPath": dst.as_posix(),
                "targetData": None,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "file (1).txt"
        assert data["files"][0]["path"] == (dst / "file (1).txt").as_posix()
        assert (src / "file.txt").exists() is False
        assert (dst / "file.txt").exists() is True
        assert (dst / "file (1).txt").exists() is True

    def test_missing_path_sends_error(self, client, tmp_path):
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": (tmp_path / "xyz").as_posix(),
                "showHiddenItems": True,
                "data": [],
            },
        )
        data = response.json
        assert response.status_code == 200
        assert data["error"]["code"] == 404
        assert data["error"]["message"] == "File Not Found"

    def test_permission_denied_sends_error(self, client, filedir):
        filedir.chmod(0o000)
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": filedir.as_posix(),
                "showHiddenItems": True,
                "data": [],
            },
        )
        filedir.chmod(mode=0o755)
        data = response.json
        assert response.status_code == 200
        assert data["error"]["code"] == 403
        assert data["error"]["message"] == "Permission Denied"


class TestFileManagerDownload:
    def test_single_file_download_action(self, client, file):
        response = client.post(
            "/file-manager/download",
            data={
                "downloadInput": json.dumps(
                    {
                        "action": "download",
                        "path": file.parent.as_posix(),
                        "names": [file.name],
                        "data": [],
                    }
                )
            },
        )
        headers = response.headers
        assert response.status_code == 200
        assert headers["Content-Disposition"] == f"attachment; filename={file.name}"
        assert headers["Content-Type"] == "text/plain; charset=utf-8"

    def test_multiple_files_download_action(self, client, tmp_path):
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = client.post(
            "/file-manager/download",
            headers=headers,
            data={
                "downloadInput": json.dumps(
                    {
                        "action": "download",
                        "path": tmp_path.as_posix(),
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

    def test_missing_path_raises_404(self, client, tmp_path):
        response = client.post(
            "/file-manager/download",
            data={
                "downloadInput": json.dumps(
                    {
                        "action": "download",
                        "path": tmp_path.as_posix(),
                        "names": ["file.txt"],
                        "data": [],
                    }
                )
            },
        )
        assert response.status_code == 404
        assert response.json == {"code": 404, "reason": "Not Found", "message": ""}


class TestFileManagerUpload:
    def test_file_upload_action(self, client, tmp_path):
        file = tmp_path / "file.txt"
        response = client.post(
            "/file-manager/upload",
            data={
                "action": "save",
                "path": tmp_path.as_posix(),
                "cancel-uploading": False,
                "uploadFiles": (io.BytesIO(b"dummy content"), file.name),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert file.exists() is True
        assert file.read_text() == "dummy content"

    def test_missing_path_raises_404(self, client, tmp_path):
        response = client.post(
            "/file-manager/upload",
            data={
                "action": "save",
                "path": (tmp_path / "xyz").as_posix(),
                "cancel-uploading": False,
                "uploadFiles": (None, "file.txt"),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 404
        assert response.json == {"code": 404, "reason": "Not Found", "message": ""}


class TestFileManagerImages:
    def test_get_image(self, client, tmp_path):
        img = tmp_path / "img.jpeg"
        img.touch()
        response = client.get(
            "/file-manager/images",
            query_string={"path": img.as_posix()},
        )
        headers = response.headers
        assert response.status_code == 200
        assert headers["Content-Disposition"] == f"inline; filename={img.name}"
        assert headers["Content-Type"] == "image/jpeg"

    def test_missing_path_raises_404(self, client, tmp_path):
        response = client.get(
            "/file-manager/images",
            query_string={"path": (tmp_path / "img.jpeg").as_posix()},
        )
        assert response.status_code == 404
        assert response.json == {"code": 404, "reason": "Not Found", "message": ""}
