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
        fs.create_file("/tmp/files/file.txt")
        file = next(iter(svc.list_files(path="/tmp/files/")))
        assert file.name == "file.txt"

    def test_list_files_on_missing_file_raises_exception(self, svc):
        with pytest.raises(FileNotFoundError) as ex:
            svc.list_files(path="/tmp/files")
        assert "No such file or directory" in str(ex.value)

    def test_list_files_on_restricted_path_raises_exception(self, svc, fs):
        fs.create_file("/tmp/files/root", st_mode=0o000)
        with pytest.raises(PermissionError) as ex:
            svc.list_files(path="/tmp/files/root")
        assert "Permission denied" in str(ex.value)

    def test_stats(self, svc, fs):
        fs.create_file("/tmp/files/file.txt")
        stats = svc.stats(path="/tmp/files/file.txt")
        assert stat.S_ISREG(stats.st_mode) is True

    def test_stats_on_missing_path_raises_exception(self, svc):
        with pytest.raises(FileNotFoundError) as ex:
            svc.stats(path="/tmp/files/missing.txt")
        assert "No such file or directory" in str(ex.value)

    def test_stats_on_restricted_path_raises_exception(self, svc, fs):
        fs.create_dir("/tmp/files/root", perm_bits=000)
        with pytest.raises(PermissionError) as ex:
            svc.stats(path="/tmp/files/root")
        assert "Permission denied" in str(ex.value)

    def test_save_file(self, svc, fs, mocker):
        file = FileStorage(filename="file.txt")
        mocker.patch.object(file, "save")
        svc.save_file(dst="/tmp/files", file=file)
        assert file.filename == "file.txt"
        assert fs.exists("/tmp/files/file.txt") is False

    def test_make_dir(self, svc, fs):
        fs.create_dir("/tmp/dirs/")
        svc.make_dir(path="/tmp/dirs/", name="dir")
        assert fs.exists("/tmp/dirs/dir") is True

    def test_make_dir_on_existing_path_throws_exception(self, svc, fs):
        fs.create_dir("/tmp/dirs/")
        with pytest.raises(FileExistsError) as ex:
            svc.make_dir(path="/tmp/", name="dirs")
        assert "File exists" in str(ex.value)

    def test_exists_path(self, svc, fs):
        filepath = "/tmp/files/file.txt"
        dirpath = "/tmp/dirs/dir/"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        assert svc.exists_path(filepath) is True
        assert svc.exists_path(dirpath) is True

    def test_remove_path(self, svc, fs):
        filepath = "/tmp/files/file.txt"
        dirpath = "/tmp/dirs/dir/"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        svc.remove_path(filepath)
        svc.remove_path(dirpath)
        assert svc.exists_path(filepath) is False
        assert svc.exists_path(dirpath) is False
        with pytest.raises(FileNotFoundError):
            assert svc.stats(path="/tmp/files/missing.txt")

    def test_move_path(self, svc, fs):
        filepath = "/tmp/files/src/file.txt"
        dirpath = "/tmp/files/src/dir"
        dst = "/tmp/files/dst/"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        fs.create_dir(dst)
        svc.move_path(src=filepath, dst=dst)
        svc.move_path(src=dirpath, dst=dst)
        assert svc.exists_path(os.path.join(dst, os.path.basename(filepath))) is True
        assert svc.exists_path(os.path.join(dst, os.path.basename(dirpath))) is True

    def test_move_missing_path_throws_exception(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.move_path(src="/tmp/files/missing", dst="")

    def test_rename_path(self, svc, fs):
        filepath = "/tmp/files/from.txt"
        dirpath = "/tmp/dirs/from"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        svc.rename_path(src=filepath, dst="/tmp/files/from.txt")
        svc.rename_path(src=dirpath, dst="/tmp/dirs/to")
        assert svc.exists_path("/tmp/files/from.txt") is True
        assert svc.exists_path("/tmp/dirs/to") is True

    def test_rename_missing_path_throws_exception(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.rename_path(src="/tmp/missing", dst="")

    def test_rename_duplicates(self, svc, fs):
        func = svc.rename_duplicates
        filepath = func(dst="/tmp/files", filename="file.txt")
        dirpath = func(dst="/tmp/dirs", filename="dir")
        assert filepath == "/tmp/files/file.txt"
        assert dirpath == "/tmp/dirs/dir"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        filepath = func(dst="/tmp/files", filename="file.txt")
        dirpath = func(dst="/tmp/dirs", filename="dir")
        assert filepath == "/tmp/files/file (1).txt"
        assert dirpath == "/tmp/dirs/dir (1)"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        filepath = func(dst="/tmp/files", filename="file.txt")
        dirpath = func(dst="/tmp/dirs", filename="dir")
        assert filepath == "/tmp/files/file (2).txt"
        assert dirpath == "/tmp/dirs/dir (2)"

    def test_create_attachment(self, svc, fs):
        filepath = "/tmp/files/file.txt"
        dirpath = "/tmp/dirs/dir"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        fileobj = svc.create_attachment(paths=(filepath, dirpath))
        names = tarfile.open(fileobj=fileobj).getnames()
        assert os.path.basename(filepath) in names
        assert os.path.basename(dirpath) in names

    def test_isfile(self, svc, fs):
        filepath = "/tmp/files/file.txt"
        dirpath = "/tmp/dirs/dir"
        fs.create_file(filepath)
        fs.create_dir(dirpath)
        assert svc.isfile(filepath)
        assert svc.isfile(dirpath) is False
        assert svc.isfile("/tmp/files/missing.txt") is False
