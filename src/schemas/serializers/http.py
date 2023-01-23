from marshmallow import fields, Schema


class HttpResponseSchema(Schema):
    code = fields.Int()
    description = fields.String()
