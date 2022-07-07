import json

from marshmallow import EXCLUDE, fields, pre_load, Schema
from marshmallow.validate import OneOf

from src.schemas.serializers.filemgr import StatsSchema


class BaseActionSchema(Schema):
    action = fields.String(
        validate=OneOf(
            ("read", "create", "delete", "rename", "search", "details", "copy", "move")
        ),
        allow_none=False,
        required=True,
    )
    path = fields.String()
    data = fields.List(fields.Nested(StatsSchema(unknown=EXCLUDE)))


class ReadActionSchema(BaseActionSchema):
    showHiddenItems = fields.Boolean()


class CreateActionSchema(BaseActionSchema):
    name = fields.String()


class DeleteActionSchema(BaseActionSchema):
    names = fields.List(fields.String())


class RenameActionSchema(BaseActionSchema):
    name = fields.String()
    newName = fields.String()


class SearchActionSchema(BaseActionSchema):
    showHiddenItems = fields.Boolean()
    caseSensitive = fields.Boolean()
    searchString = fields.String()


class DetailsActionSchema(BaseActionSchema):
    names = fields.List(fields.String())


class CopyActionSchema(BaseActionSchema):
    names = fields.List(fields.String())
    renameFiles = fields.List(fields.String())
    targetPath = fields.String()
    targetData = fields.Nested(StatsSchema(unknown=EXCLUDE), allow_none=True)


class MoveActionSchema(BaseActionSchema):
    names = fields.List(fields.String())
    renameFiles = fields.List(fields.String())
    targetPath = fields.String()
    targetData = fields.Nested(StatsSchema(unknown=EXCLUDE), allow_none=True)


class UploadSchema(Schema):
    action = fields.String(
        validate=OneOf(("save", "remove")),
        allow_none=False,
        required=True,
    )
    path = fields.String()
    cancel_uploading = fields.String(data_key="cancel-uploading")


class DownloadSchema(Schema):
    class DownloadInputSchema(BaseActionSchema):
        action = fields.String(
            validate=OneOf(("download",)),
            allow_none=False,
            required=True,
        )
        path = fields.String()
        data = fields.List(fields.Nested(StatsSchema(unknown=EXCLUDE)))
        names = fields.List(fields.String())

    downloadInput = fields.Nested(DownloadInputSchema())

    @pre_load
    def parser(self, data, **_):
        parsed = data.to_dict()
        parsed["downloadInput"] = json.loads(parsed["downloadInput"])
        return parsed
