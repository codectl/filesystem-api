import pytest

from src.services.filemgr import FileManagerSvc


@pytest.fixture(scope="class")
def svc():
    return FileManagerSvc(username="test")


class TestFilesystemSvc:
    def test_list(self, svc, tmp_path):
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        (tmp_path / ".file3.txt").touch()
        assert len(svc.list(path=tmp_path, show_hidden=False)) == 2
        assert len(svc.list(path=tmp_path, show_hidden=True)) == 3
        assert len(svc.list(path=tmp_path, substr="file2")) == 1

    def test_list_on_missing_file_raises_exception(self, svc, tmp_path):
        with pytest.raises(FileNotFoundError) as ex:
            svc.list(path=tmp_path / "xyz")
        assert "No such file or directory" in str(ex.value)

    def test_list_on_restricted_dir_raises_exception(self, svc, filedir):
        filedir.chmod(mode=0o000)
        with pytest.raises(PermissionError) as ex:
            svc.list(path=filedir)
        assert "Permission denied" in str(ex.value)

    def test_stats(self, svc, file):
        stats = svc.stats(path=file)
        assert stats["name"] == "file.txt"
        assert stats["path"] == file.as_posix()
        assert stats["type"] == ".txt"
        assert stats["isFile"] is True
        assert stats["hasChild"] is False
