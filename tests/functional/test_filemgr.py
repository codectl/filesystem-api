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
