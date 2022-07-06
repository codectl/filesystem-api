import pytest

from src.services.filemgr import FileManagerSvc


@pytest.fixture(scope="class")
def svc():
    return FileManagerSvc(username="test")


class TestFilesystemSvc:
    def test_list_files(self, svc, fs):
        fs.create_file("/tmp/file1.txt")
        fs.create_file("/tmp/file2.txt")
        fs.create_file("/tmp/.file3.txt")
        assert len(svc.list_files(path="/tmp", show_hidden=False)) == 2
        assert len(svc.list_files(path="/tmp", show_hidden=True)) == 3
        assert len(svc.list_files(path="/tmp", substr="file2")) == 1

    def test_list_files_on_missing_file_raises_exception(self, svc):
        with pytest.raises(FileNotFoundError) as ex:
            svc.list_files(path="/tmp/missing.txt")
        assert "No such file or directory" in str(ex.value)

    def test_list_files_on_restricted_path_raises_exception(self, svc, fs):
        fs.create_file("/tmp/root", st_mode=0o000)
        with pytest.raises(PermissionError) as ex:
            svc.list_files(path="/tmp/root")
        assert "Permission denied" in str(ex.value)

    def test_stats(self, svc, fs):
        fs.create_file("/tmp/file.txt")
        stats = svc.stats(path="/tmp/file.txt")
        assert stats["name"] == "file.txt"
        assert stats["path"] == "/tmp/file.txt"
        assert stats["type"] == ".txt"
        assert stats["isFile"] is True
        assert stats["hasChild"] is False
