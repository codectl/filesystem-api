from marshmallow import fields, Schema


class FileMgrStatsSchema(Schema):
    name = fields.String()
    dateCreated = fields.String()
    dateModified = fields.String()
    filterPath = fields.String()
    hasChild = fields.Boolean()
    isFile = fields.Boolean()
    size = fields.Number()
    type = fields.String()


class FileMgrErrorSchema(Schema):
    code = fields.Number()
    message = fields.Number()
    fileExists = fields.List(fields.String())


class FileMgrDetailsSchema(FileMgrStatsSchema):
    multipleFiles = fields.Boolean()


class FileMgrResponseSchema(Schema):
    cwd = fields.Nested(FileMgrStatsSchema())
    files = fields.List(fields.Nested(FileMgrStatsSchema()))
