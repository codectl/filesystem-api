from datetime import datetime
import os
import pathlib
import re

from services.filesystem import FilesystemSvc

__all__ = ("FileManagerSvc",)


class FileManagerSvc(FilesystemSvc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def list_files(self, path, show_hidden=False, substr=None):
        """Override"""
        regex = rf".*{(substr or '').strip('*')}.*"
        files = super().list_files(path, show_hidden=show_hidden)
        return [filename for filename in files if re.match(regex, filename)]

    def stats(self, path):
        """Override"""
        return self.stats_mapper(path, stats=super().stats(path))

    @staticmethod
    def stats_mapper(path: str, stats: os.stat_result) -> dict:
        path = os.path.join(os.path.sep, path.strip(os.path.sep))
        isdir = os.path.isdir(path)
        return {
            "name": os.path.basename(path),
            "path": path,
            "filterPath": os.path.join(os.path.dirname(path), ""),
            "size": stats.st_size,
            "isFile": not isdir,
            "dateModified": datetime.fromtimestamp(stats.st_mtime),
            "dateCreated": datetime.fromtimestamp(stats.st_ctime),
            "type": pathlib.Path(path).suffix,
            "hasChild": bool(next(os.walk(path), ((), ()))[1]) if isdir else False,
            "mode": stats.st_mode,
        }
