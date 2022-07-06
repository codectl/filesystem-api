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
    def test_list_files(self, svc, fs):
        fs.create_file("/tmp/file.txt")
        file = next(iter(svc.list_files(path="/tmp/")))
        assert file.name == "file.txt"

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
        assert stat.S_ISREG(stats.st_mode) is True

    def test_stats_on_missing_path_raises_exception(self, svc):
        with pytest.raises(FileNotFoundError) as ex:
            svc.stats(path="/tmp/missing.txt")
        assert "No such file or directory" in str(ex.value)

    def test_stats_on_restricted_path_raises_exception(self, svc, fs):
        fs.create_dir("/tmp/root", perm_bits=000)
        with pytest.raises(PermissionError) as ex:
            svc.stats(path="/tmp/root")
        assert "Permission denied" in str(ex.value)

    def test_save_file(self, svc, fs, mocker):
        file = FileStorage(filename="file.txt")
        mocker.patch.object(file, "save")
        svc.save_file(dst="/tmp", file=file)
        assert file.filename == "file.txt"
        assert fs.exists("/tmp/file.txt") is False

    def test_make_dir(self, svc, fs):
        fs.create_dir("/tmp/")
        svc.make_dir(path="/tmp/", name="dir")
        assert fs.exists("/tmp/dir") is True

    def test_make_dir_on_existing_path_throws_exception(self, svc, fs):
        fs.create_dir("/tmp/dir/")
        with pytest.raises(FileExistsError) as ex:
            svc.make_dir(path="/tmp/", name="dir")
        assert "File exists" in str(ex.value)

    def test_exists_path(self, svc, fs):
        filepath = "/tmp/file.txt"
        dirpath = "/tmp/dir/"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        assert svc.exists_path(filepath) is True
        assert svc.exists_path(dirpath) is True

    def test_remove_path(self, svc, fs):
        filepath = "/tmp/file.txt"
        dirpath = "/tmp/dir/"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        svc.remove_path(filepath)
        svc.remove_path(dirpath)
        assert svc.exists_path(filepath) is False
        assert svc.exists_path(dirpath) is False
        with pytest.raises(FileNotFoundError):
            assert svc.stats(path="/tmp/missing.txt")

    def test_move_path(self, svc, fs):
        filepath = "/tmp/src/file.txt"
        dirpath = "/tmp/src/dir"
        dst = "/tmp/dst/"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        fs.create_dir(dst)
        svc.move_path(src=filepath, dst=dst)
        svc.move_path(src=dirpath, dst=dst)
        assert svc.exists_path(os.path.join(dst, os.path.basename(filepath))) is True
        assert svc.exists_path(os.path.join(dst, os.path.basename(dirpath))) is True

    def test_move_missing_path_throws_exception(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.move_path(src="/tmp/missing", dst="")

    def test_rename_path(self, svc, fs):
        filepath = "/tmp/from.txt"
        dirpath = "/tmp/from"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        svc.rename_path(src=filepath, dst="/tmp/from.txt")
        svc.rename_path(src=dirpath, dst="/tmp/to")
        assert svc.exists_path("/tmp/from.txt") is True
        assert svc.exists_path("/tmp/to") is True

    def test_rename_missing_path_throws_exception(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.rename_path(src="/tmp/missing", dst="")

    def test_rename_duplicates(self, svc, fs):
        func = svc.rename_duplicates
        filepath = func(dst="/tmp", filename="file.txt")
        dirpath = func(dst="/tmp", filename="dir")
        assert filepath == "/tmp/file.txt"
        assert dirpath == "/tmp/dir"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        filepath = func(dst="/tmp", filename="file.txt")
        dirpath = func(dst="/tmp", filename="dir")
        assert filepath == "/tmp/file (1).txt"
        assert dirpath == "/tmp/dir (1)"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        filepath = func(dst="/tmp", filename="file.txt")
        dirpath = func(dst="/tmp", filename="dir")
        assert filepath == "/tmp/file (2).txt"
        assert dirpath == "/tmp/dir (2)"

    def test_create_attachment(self, svc, fs):
        filepath = "/tmp/file.txt"
        dirpath = "/tmp/dir"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        fileobj = svc.create_attachment(paths=(filepath, dirpath))
        names = tarfile.open(fileobj=fileobj).getnames()
        assert os.path.basename(filepath) in names
        assert os.path.basename(dirpath) in names

    def test_isfile(self, svc, fs):
        filepath = "/tmp/file.txt"
        dirpath = "/tmp/dir"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        assert svc.isfile(filepath)
        assert svc.isfile(dirpath) is False
        assert svc.isfile("/tmp/missing.txt") is False
