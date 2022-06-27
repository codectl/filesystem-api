from datetime import datetime
import io
import os
import pathlib
import re
import shutil
import tarfile

from src import utils

__all__ = ("FileManagerSvc",)


class user_ctx:
    def __init__(self, username):
        self.username = username
        self.uid = os.getuid()
        self.gid = os.getuid()

    def __enter__(self):
        os.setuid(utils.user_uid(self.username))
        os.setgid(utils.user_gid(self.username))

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.setuid(self.uid)
        os.setgid(self.gid)


class FileManagerSvc:
    def __init__(self, username=None):
        self.username = str(username) if username else None

    def list_files(self, path, show_hidden=False, substr=None):
        regex = rf".*{(substr or '').strip('*')}.*"
        if not show_hidden:
            regex = "".join((r"^(?!\.)", regex))

        return [
            os.path.join(path, file.name)
            for file in iter(os.scandir(path=path))
            if re.match(regex, file.name)
        ]

    def stats(self, path):
        path = os.path.join(os.path.sep, path.strip(os.path.sep))
        stats = os.stat(path, follow_symlinks=False)
        isdir = os.path.isdir(path)
        return {
            "name": os.path.basename(path),
            "path": path,
            "filterPath": os.path.join(os.path.dirname(path), ""),
            "size": stats.st_size,
            "isFile": not isdir,
            "dateModified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "dateCreated": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "type": pathlib.Path(path).suffix,
            "hasChild": bool(next(os.walk(path), ((), ()))[1]) if isdir else False,
            "mode": stats.st_mode,
        }

    def create_dir(self, path, name):
        os.mkdir(os.path.join(path, name))

    def remove_path(self, path):
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    def move_path(self, src, dst):
        dst = self.rename_duplicates(dst=dst, filename=os.path.basename(src))
        shutil.move(src, dst)

    def rename_path(self, src, dst):
        os.rename(src, dst)

    def copy_path(self, src, dst):
        dst = self.rename_duplicates(dst=dst, filename=os.path.basename(src))
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    @classmethod
    def rename_duplicates(cls, dst, filename, count=0):
        if count > 0:
            base, extension = os.path.splitext(filename)
            candidate = f"{base}({count}){extension}"
        else:
            candidate = filename
        path = os.path.join(dst, candidate)
        if os.path.exists(path):
            return cls.rename_duplicates(dst, filename, count + 1)
        else:
            return path

    def create_attachment(self, paths=()):
        obj = io.BytesIO()
        with tarfile.open(fileobj=obj, mode="w|gz") as tar:
            for path in paths:
                arcname = os.path.basename(path)  # keep path relative
                tar.add(path, arcname=arcname)
        obj.seek(0)
        return obj
