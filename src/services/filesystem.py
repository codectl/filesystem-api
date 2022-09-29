import io
import tarfile
import os
import re
import shutil
from pathlib import Path

from impersonation import impersonate

__all__ = ("FilesystemSvc",)


@impersonate
class FilesystemSvc:
    @staticmethod
    def list(path, show_hidden=False) -> list[Path]:
        regex = r".*"
        if not show_hidden:
            regex = "".join((r"^(?!\.)", regex))
        return [p for p in Path(path).iterdir() if re.match(regex, p.name)]

    @staticmethod
    def stats(path) -> os.stat_result:
        return Path(path).stat()

    @staticmethod
    def create(path, content=b""):
        f = Path(path)
        f.write_bytes(content)

    @staticmethod
    def mkdir(path):
        Path(path).mkdir()

    @staticmethod
    def exists(path):
        return Path(path).exists()

    @staticmethod
    def delete(path):
        p = Path(path)
        if p.is_dir():
            p.rmdir()
        else:
            p.unlink()

    @classmethod
    def move(cls, src, dst):
        src = Path(src)
        dst = cls.rename_duplicates(dst=dst, filename=src.name)
        shutil.move(src, dst)
        return dst

    @staticmethod
    def rename(src, dst):
        Path(src).rename(dst)

    @classmethod
    def copy(cls, src, dst):
        src = Path(src)
        dst = cls.rename_duplicates(dst=dst, filename=src.name)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return dst

    @classmethod
    def rename_duplicates(cls, dst, filename, count=0):
        if count > 0:
            base, extension = os.path.splitext(filename)
            candidate = f"{base} ({count}){extension}"
        else:
            candidate = filename
        path = os.path.join(dst, candidate)
        if os.path.exists(path):
            return cls.rename_duplicates(dst, filename, count + 1)
        else:
            return path

    @staticmethod
    def create_attachment(paths=()):
        obj = io.BytesIO()
        with tarfile.open(fileobj=obj, mode="w|gz") as tar:
            for path in paths:
                arch_name = os.path.basename(path)  # keep path relative
                tar.add(path, arcname=arch_name)
        obj.seek(0)
        return obj

    @staticmethod
    def is_file(path):
        return Path(path).is_file()
