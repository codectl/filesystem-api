from marshmallow import fields, Schema
from schemas.serializers.http import HttpResponseSchema


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


class StatsResponseSchema(Schema):
    cwd = fields.Nested(StatsSchema)
    files = fields.List(fields.Nested(StatsSchema))


class ErrorSchema(HttpResponseSchema):
    fileExists = fields.List(fields.String())


class ErrorResponseSchema(Schema):
    error = fields.Nested(ErrorSchema)


class DetailsResponseSchema(Schema):
    details = fields.Nested(DetailsSchema)


def dump_stats(**kwargs):
    return StatsResponseSchema().dump(kwargs)


def dump_error(**kwargs):
    return ErrorResponseSchema().dump({"error": kwargs})


def dump_details(**kwargs):
    return DetailsResponseSchema().dump({"details": kwargs})
