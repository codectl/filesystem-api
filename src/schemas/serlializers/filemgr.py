from marshmallow import fields, Schema


class StatsSchema(Schema):
    name = fields.String()
    path = fields.String()
    dateCreated = fields.String()
    dateModified = fields.String()
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


class DetailsSchema(StatsSchema):
    multipleFiles = fields.Boolean()


class ResponseSchema(Schema):
    cwd = fields.Nested(StatsSchema)
    files = fields.List(fields.Nested(StatsSchema))
