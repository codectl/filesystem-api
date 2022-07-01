from marshmallow import fields, Schema
from marshmallow.validate import OneOf

from src.schemas.serlializers.filemgr import FileMgrStatsSchema


class FileMgrBaseRequest(Schema):
    action = fields.String(
        validate=OneOf(
            ["read", "create", "delete", "rename", "search", "details", "copy", "move"]
        ),
        allow_none=False,
    )
    path = fields.String()
    data = fields.Nested(FileMgrStatsSchema())


class FileMgrReadAction(FileMgrBaseRequest):
    showHiddenItems = fields.Boolean()


class FileMgrCreateAction(FileMgrBaseRequest):
    name = fields.String()


class FileMgrRenameAction(FileMgrBaseRequest):
    name = fields.String()
    newName = fields.String()


class FileMgrDeleteAction(FileMgrBaseRequest):
    names = fields.List(fields.String())


class FileMgrDetailsAction(FileMgrBaseRequest):
    names = fields.List(fields.String())


class FileMgrSearchAction(FileMgrBaseRequest):
    showHiddenItems = fields.Boolean()
    caseSensitive = fields.Boolean()
    searchString = fields.String()


class FileMgrCopyAction(FileMgrBaseRequest):
    names = fields.List(fields.String())
    targetPath = fields.String()
    renameFiles = fields.List(fields.String())


class FileMgrMoveAction(FileMgrBaseRequest):
    names = fields.List(fields.String())
    targetPath = fields.String()
    renameFiles = fields.List(fields.String())
