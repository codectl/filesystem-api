import io
import tarfile
import os
import re
import shutil

from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from src.services.auth import impersonate

__all__ = ("FilesystemSvc",)


class FilesystemSvc:
    def __init__(self, username=None):
        self.username = str(username) if username else None

    @impersonate()
    def list_files(self, path, show_hidden=False) -> list[os.DirEntry]:
        regex = r".*"
        if not show_hidden:
            regex = "".join((r"^(?!\.)", regex))
        return [
            file for file in iter(os.scandir(path=path)) if re.match(regex, file.name)
        ]

    @impersonate()
    def stats(self, path) -> os.stat_result:
        return os.stat(os.path.normpath(path), follow_symlinks=False)

    @impersonate()
    def save_file(self, dst, file: FileStorage):
        filename = secure_filename(file.filename)
        file.save(os.path.join(dst, filename))

    @impersonate()
    def make_dir(self, path, name):
        os.mkdir(os.path.join(path, name))

    @impersonate()
    def exists_path(self, path):
        return os.path.exists(path)

    @impersonate()
    def remove_path(self, path):
        if not self.exists_path(path):
            raise FileNotFoundError
        elif os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    @impersonate()
    def move_path(self, src, dst):
        dst = self.rename_duplicates(dst=dst, filename=os.path.basename(src))
        shutil.move(src, dst)

    @impersonate()
    def rename_path(self, src, dst):
        os.rename(src, dst)

    @impersonate()
    def copy_path(self, src, dst):
        dst = self.rename_duplicates(dst=dst, filename=os.path.basename(src))
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    @impersonate()
    def rename_duplicates(self, dst, filename, count=0):
        if count > 0:
            base, extension = os.path.splitext(filename)
            candidate = f"{base} ({count}){extension}"
        else:
            candidate = filename
        path = os.path.join(dst, candidate)
        if os.path.exists(path):
            return self.rename_duplicates(dst, filename, count + 1)
        else:
            return path

    @impersonate()
    def create_attachment(self, paths=()):
        obj = io.BytesIO()
        with tarfile.open(fileobj=obj, mode="w|gz") as tar:
            for path in paths:
                arcname = os.path.basename(path)  # keep path relative
                tar.add(path, arcname=arcname)
        obj.seek(0)
        return obj

    @impersonate()
    def isfile(self, path):
        return os.path.isfile(path)
