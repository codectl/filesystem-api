import os
import stat
import tarfile

import pytest
from werkzeug.datastructures import FileStorage

from src.services.filesystem import FilesystemSvc


@pytest.fixture(scope="class")
def svc():
    return FilesystemSvc(username="test")


class TestFilesystemSvc:
    def test_list(self, svc, file):
        dirpath = os.path.dirname(file)
        files = svc.list(path=dirpath)
        assert any(f.name == file.name for f in files)

    def test_list_on_missing_file_raises_exception(self, svc, file):
        svc.delete(file)
        with pytest.raises(FileNotFoundError) as ex:
            svc.list(path=file)
        assert "No such file or directory" in str(ex.value)

    def test_list_restricted_dir_raises_exception(self, svc, filedir):
        filedir.chmod(0o000)
        with pytest.raises(PermissionError) as ex:
            svc.list(path=filedir)
        filedir.chmod(0o755)
        assert "Permission denied" in str(ex.value)

    def test_stats(self, svc, file):
        stats = svc.stats(path=file)
        assert stat.S_ISREG(stats.st_mode) is True

    def test_stats_on_missing_file_raises_exception(self, svc, file):
        svc.delete(file)
        with pytest.raises(FileNotFoundError) as ex:
            svc.list(path=file)
        assert "No such file or directory" in str(ex.value)

    def test_save(self, svc, file, mocker):
        f = FileStorage(filename=file.name)
        mocker.patch.object(f, "save")
        svc.save(dst=os.path.dirname(file), file=f)
        assert f.filename == file.name

    def test_mkdir(self, svc, filedir):
        dirpath = filedir / "new-dir"
        svc.mkdir(path=dirpath)
        assert svc.exists(dirpath) is True
        svc.delete(path=dirpath)
        assert svc.exists(dirpath) is False

    def test_mkdir_on_existing_path_throws_exception(self, svc, filedir):
        with pytest.raises(FileExistsError) as ex:
            svc.mkdir(path=filedir)
        assert "File exists" in str(ex.value)

    def test_exists(self, svc, file, filedir):
        assert svc.exists(file) is True
        assert svc.exists(filedir) is True
        assert svc.exists(filedir / "xyz") is False

    def test_delete(self, svc, file, filedir):
        svc.delete(file)
        assert svc.exists(file) is False
        assert svc.exists(filedir / "xyz") is False
        with pytest.raises(FileNotFoundError):
            assert svc.stats(path=file)
            assert svc.stats(path=filedir / "xyz")

    def test_move(self, svc, file, tmp_path):
        dst = tmp_path / "dst"
        filedir = tmp_path / "dir"
        dst.mkdir()
        filedir.mkdir()
        svc.move(src=file, dst=dst)
        svc.move(src=filedir, dst=dst)
        assert svc.exists(dst / file.name) is True
        assert svc.exists(dst / filedir.name) is True

    def test_move_missing_path_throws_exception(self, svc, file, filedir):
        with pytest.raises(FileNotFoundError):
            svc.move(src=file, dst=filedir / "xyz")

    def test_rename(self, svc, tmp_path):
        file = tmp_path / "file1.txt"
        file.touch()
        filedir = tmp_path / "dir1"
        filedir.mkdir()
        svc.rename(src=file, dst=file.parent / "file2.txt")
        svc.rename(src=filedir, dst=filedir.parent / "dir2")
        assert svc.exists(path=file.parent / "file1.txt") is False
        assert svc.exists(path=file.parent / "file2.txt") is True
        assert svc.exists(path=filedir.parent / "dir1") is False
        assert svc.exists(path=filedir.parent / "dir2") is True

    def test_rename_missing_path_throws_exception(self, svc, file, filedir):
        with pytest.raises(FileNotFoundError):
            svc.rename(src=filedir / "xyz", dst=filedir)

    def test_rename_duplicates(self, svc, file, filedir, tmp_path_factory):
        func = svc.rename_duplicates
        f = func(dst=filedir, filename="file.txt")
        d = func(dst=filedir, filename="dir")
        assert f == (filedir / "file.txt").as_posix()
        assert d == (filedir / "dir").as_posix()
        (filedir / "file.txt").touch()
        (filedir / "dir").mkdir()
        d = func(dst=filedir, filename="dir")
        f = func(dst=filedir, filename="file.txt")
        assert f == (filedir / "file (1).txt").as_posix()
        assert d == (filedir / "dir (1)").as_posix()
        (filedir / "file (1).txt").touch()
        (filedir / "dir (1)").mkdir()
        f = func(dst=filedir, filename="file.txt")
        d = func(dst=filedir, filename="dir")
        assert f == (filedir / "file (2).txt").as_posix()
        assert d == (filedir / "dir (2)").as_posix()

    def test_create_attachment(self, svc, file, filedir):
        fileobj = svc.create_attachment(paths=(file, filedir))
        names = tarfile.open(fileobj=fileobj).getnames()
        assert file.name in names
        assert filedir.name in names

    def test_is_file(self, svc, file, filedir):
        assert svc.is_file(file) is True
        assert svc.is_file(filedir) is False
        assert svc.is_file(filedir / "dir") is False
