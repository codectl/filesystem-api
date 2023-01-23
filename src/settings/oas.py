from dataclasses import asdict

from apispec.ext.marshmallow import OpenAPIConverter, resolver

from src.schemas.serializers.http import HttpResponseSchema

__all__ = (
    "create_spec_converter",
    "base_template",
    "swagger_configs",
)


def create_spec_converter(openapi_version):
    return OpenAPIConverter(
        openapi_version=openapi_version,
        schema_name_resolver=lambda schema: None,
        spec=None,
    )


def base_template(
    openapi_version, info=None, servers=(), auths=(), tags=(), responses=()
):
    """Base OpenAPI template."""
    global converter
    return {
        "openapi": openapi_version,
        "info": info or {},
        "servers": servers,
        "tags": tags,
        "components": {
            "securitySchemes": {**{auth.__name__: asdict(auth()) for auth in auths}},
            "responses": {
                response.reason.replace(" ", ""): {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/HttpResponse"}
                        }
                    },
                }
                for response in responses
            },
            "schemas": {
                resolver(HttpResponseSchema): {
                    **converter.schema2jsonschema(schema=HttpResponseSchema)
                }
            }
            if responses
            else {},
        },
    }


def swagger_configs(app_root="/"):
    prefix = "" if app_root == "/" else app_root
    return {
        "url_prefix": prefix,
        "swagger_route": "/",
        "swagger_static": "/static",
        "swagger_favicon": "favicon.ico",
        "swagger_hide_bar": True,
    }
