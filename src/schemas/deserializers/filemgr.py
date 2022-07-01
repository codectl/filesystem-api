from marshmallow import fields, Schema, validate
from src.schemas.serlializers.filemgr import FileMgrStatsSchema


class FileMgrRequest(Schema):
    action = fields.String(
        validate=validate.OneOf([
            "read", "create", "delete",
                                 "rename", "search", "details",
                                 "copy", "move"])
    )
    path = fields.String()
    targetPath = fields.String()
    name = fields.String()
    names = fields.List(fields.String())
    newName = fields.String()
    renameFiles = fields.List(fields.String())
    showHiddenItems = fields.Boolean()
    caseSensitive = fields.Boolean()
    searchString = fields.String()
    data = fields.Nested(FileMgrStatsSchema())
