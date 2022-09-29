import os
import re
from datetime import datetime
from pathlib import Path

from src.services.filesystem import FilesystemSvc

__all__ = ("FileManagerSvc",)


class FileManagerSvc(FilesystemSvc):
    @staticmethod
    def list(path, show_hidden=False, substr=None):
        """Override"""
        regex = rf".*{(substr or '').strip('*')}.*"
        files = FilesystemSvc.list(path, show_hidden=show_hidden)
        return [file for file in files if re.match(regex, file.name)]

    @classmethod
    def stats(cls, path) -> dict:
        """Override"""
        return cls.stats_mapper(path, stats=FilesystemSvc.stats(path))

    @staticmethod
    def stats_mapper(path: str, stats: os.stat_result) -> dict:
        path = Path(path)
        return {
            "name": path.name,
            "path": path.as_posix(),
            "filterPath": os.path.join(path.parent, ""),
            "size": stats.st_size,
            "isFile": not path.is_dir(),
            "dateModified": datetime.fromtimestamp(stats.st_mtime),
            "dateCreated": datetime.fromtimestamp(stats.st_ctime),
            "type": path.suffix,
            "hasChild": bool(next(path.iterdir(), False)) if path.is_dir() else False,
            "mode": stats.st_mode,
        }
