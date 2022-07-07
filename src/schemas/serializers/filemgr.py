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


class BaseResponseSchema(Schema):
    cwd = fields.Nested(StatsSchema)
    files = fields.List(fields.Nested(StatsSchema))


class StatsResponseSchema(BaseResponseSchema):
    pass


class ErrorSchema(HttpResponseSchema):
    fileExists = fields.List(fields.String())


class ErrorResponseSchema(BaseResponseSchema):
    error = fields.Nested(ErrorSchema)


class DetailsResponseSchema(BaseResponseSchema):
    details = fields.Nested(DetailsSchema)


def dump_stats(**kwargs):
    return StatsResponseSchema().dump(kwargs)


def dump_error(**kwargs):
    return ErrorResponseSchema().dump({**{"error": kwargs}, **kwargs})


def dump_details(**kwargs):
    return DetailsResponseSchema().dump({**{"details": kwargs}, **kwargs})
