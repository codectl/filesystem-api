from marshmallow import fields, Schema


class StatsSchema(Schema):
    name = fields.String()
    path = fields.String()
    dateCreated = fields.DateTime()
    dateModified = fields.DateTime()
    filterPath = fields.String()
    hasChild = fields.Boolean()
    isFile = fields.Boolean()
    size = fields.Number()
    type = fields.String()
    mode = fields.Integer()


class ErrorSchema(Schema):
    code = fields.Number()
    message = fields.Number()
    fileExists = fields.List(fields.String())


class DetailsSchema(Schema):
    name = fields.String()
    location = fields.String()
    created = fields.DateTime()
    modified = fields.DateTime()
    isFile = fields.Boolean()
    size = fields.String()
    multipleFiles = fields.Boolean()


class ResponseSchema(Schema):
    cwd = fields.Nested(StatsSchema)
    files = fields.List(fields.Nested(StatsSchema))
