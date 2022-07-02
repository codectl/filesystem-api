from marshmallow import fields, Schema
from schemas.serlializers.http import HttpResponseSchema


class ErrorSchema(HttpResponseSchema):
    fileExists = fields.List(fields.String())


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


def dump_error(**kwargs):
    return {"error": ErrorSchema().dump(**kwargs)}


def dump_response(**kwargs):
    return ResponseSchema.dump(**kwargs)


def dump_details(**kwargs):
    return {"details": DetailsSchema().dump(**kwargs)}
