import io
import tarfile
import os
import re
import shutil
from pathlib import Path

from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from src.services.auth import as_user

__all__ = ("FilesystemSvc",)


@as_user
class FilesystemSvc:
    def __init__(self, username=None):
        self.username = str(username) if username else None

    def list(self, path, show_hidden=False) -> list[Path]:
        regex = r".*"
        if not show_hidden:
            regex = "".join((r"^(?!\.)", regex))
        return [p for p in Path(path).iterdir() if re.match(regex, p.name)]

    def stats(self, path) -> os.stat_result:
        return Path(path).stat()

    def save(self, dst, file: FileStorage):
        filename = secure_filename(file.filename)
        file.save(os.path.join(dst, filename))

    def mkdir(self, path):
        Path(path).mkdir()

    def exists(self, path):
        return Path(path).exists()

    def delete(self, path):
        p = Path(path)
        if p.is_dir():
            p.rmdir()
        else:
            p.unlink()

    def move(self, src, dst):
        src = Path(src)
        dst = self.rename_duplicates(dst=dst, filename=src.name)
        shutil.move(src, dst)
        return dst

    def rename(self, src, dst):
        Path(src).rename(dst)

    def copy(self, src, dst):
        src = Path(src)
        dst = self.rename_duplicates(dst=dst, filename=src.name)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return dst

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

    def create_attachment(self, paths=()):
        obj = io.BytesIO()
        with tarfile.open(fileobj=obj, mode="w|gz") as tar:
            for path in paths:
                arch_name = os.path.basename(path)  # keep path relative
                tar.add(path, arcname=arch_name)
        obj.seek(0)
        return obj

    def is_file(self, path):
        return Path(path).is_file()
