from datetime import datetime
import os
import pathlib
import re
import shutil
import subprocess

from werkzeug.utils import secure_filename

from src import utils

__all__ = ("FilesystemSvc",)


class FilesystemSvc:
    def __init__(self, username=None):
        self.username = str(username) if username else None

    def list_files(self, path, flags=""):
        return self._run(cmd=f"ls {flags} {path}", user=self.username)

    def attachment(self, path, mode=None) -> (str, bytes):
        """Get attachable file tuple consisting of name and bytes content."""
        path = utils.normpath(path)
        if utils.isfile(mode):
            cmd = f"cat {path}"
            stream = self._run(cmd=cmd, user=self.username, universal_newlines=False)
            filename = os.path.basename(path)
            content = io.BytesIO(stream)
            return filename, content
        elif utils.isdir(mode):
            archive_dir = os.path.dirname(path)
            archive_name = os.path.basename(path)
            cmd = f"tar -cvpf - -C {archive_dir} {archive_name}"
            stream = self._run(cmd=cmd, user=self.username, universal_newlines=False)
            filename = f"{os.path.basename(path)}.tar.gz"
            content = io.BytesIO(stream)
            return filename, content

        raise ValueError("unsupported file mode")

    def upload_files(self, path, files=(), update=False):
        """Upload given files to the specified path ensuring
        files do not already exist.
        """
        path = f"{utils.normpath(path)}/"
        path_files = self.list_files(path)
        for file in files:
            filename = secure_filename(file.filename)
            if update and filename not in path_files:
                raise FileNotFoundError("file does not exist")
            elif not update and filename in path_files:
                raise FileExistsError("file already exists")

        for file in files:
            filename = secure_filename(file.filename)
            dst = f"{path}/{filename}"
            self._run(
                cmd=f"tee {dst}",
                stdin=file,
                stdout=subprocess.DEVNULL,
                user=self.username,
            )

    def delete_file(self, path):
        self._run(
            cmd=f"rm {path}",
            stdout=subprocess.DEVNULL,
            user=self.username,
        )

    @classmethod
    def _run(cls, cmd, **kwargs):
        try:
            stdout = utils.shell(cmd, **kwargs)
        except subprocess.CalledProcessError as ex:
            cls.raise_error(ex.stderr)
        else:
            return stdout.splitlines() if isinstance(stdout, str) else stdout

    @staticmethod
    def raise_error(stderr):
        err = stderr.split(":")[-1].strip().lower()
        if err == "no such file or directory":
            raise FileNotFoundError(err)
        elif err == "permission denied":
            raise PermissionError(err)
        elif err == "is a directory":
            raise IsADirectoryError(err)
        elif err == "not a directory":
            raise NotADirectoryError(err)
        else:
            raise Exception(err)
