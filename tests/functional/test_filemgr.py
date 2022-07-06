class TestFileManagerActions:

    def test_read_action_returns_200(self, client, fs):
        fs.create_file("/tmp/file1.txt")
        fs.create_file("/tmp/.file2.txt")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "read",
                "path": "/tmp",
                "showHiddenItems": True,
                "data": []
            }
        )
        data = response.json
        assert response.status_code == 200
        assert data["cwd"]["name"] == "tmp"
        assert data["cwd"]["path"] == "/tmp"
        assert len(data["files"]) == 2

    def test_create_action_returns_200(self, client, fs):
        fs.create_dir("/tmp")
        response = client.post(
            "/file-manager/actions",
            json={
                "action": "create",
                "path": "/tmp",
                "name": "dir",
                "data": []
            }
        )
        data = response.json
        assert response.status_code == 200
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "dir"
        assert data["files"][0]["path"] == "/tmp/dir"
        assert data["files"][0]["isFile"] is False
        assert data["files"][0]["hasChild"] is False
        assert fs.exists("/tmp/dir")
