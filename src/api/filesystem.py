from flask import Blueprint, jsonify, request, send_file
from flask_restful import Api, Resource
from http.client import HTTPException

from src import utils
from src.services.filesystem import FilesystemSvc
from src.api.auth import current_username, requires_auth

blueprint = Blueprint("filesystem", __name__)
api = Api(blueprint)


@api.resource("/<path:path>", endpoint="fs")
class Filesystem(Resource):
    # @requires_auth(schemes=["basic"])
    def get(self, path):
        """
        List files in given path.
        ---
        parameters:
        - in: path
          name: path
          schema:
            type: string
          required: true
          description: the path to list content from
        tags:
            - filesystem
        security:
            - BasicAuth: []
        responses:
            200:
                description: Ok
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                type: string
                    application/octet-stream:
                        schema:
                            type: string
                            format: binary
            400:
                $ref: "#/components/responses/BadRequest"
            401:
                $ref: "#/components/responses/Unauthorized"
            403:
                $ref: "#/components/responses/Forbidden"
            404:
                $ref: "#/components/responses/NotFound"
        """
        path = utils.normpath(path)
        username = current_username
        fs = FilesystemSvc(username=username)
        try:
            accept = request.headers.get("accept", "application/json")
            if accept == "application/json":
                return jsonify(fs.list_files(path=path))
            elif accept == "application/octet-stream":
                stats = fs.list_files(path=path, flags="-dlL")[0]
                mode = utils.file_mode(stats=stats)
                name, content = fs.attachment(path=path, mode=mode)
                return send_file(content, as_attachment=True)
            raise HTTPException("unsupported 'accept' HTTP header")

        except PermissionError as ex:
            utils.abort_with(code=403, message=str(ex))
        except FileNotFoundError as ex:
            utils.abort_with(code=404, message=str(ex))
        except Exception as ex:
            utils.abort_with(code=400, message=str(ex))

    @requires_auth(schemes=["basic"])
    def post(self, path):
        """
        Create files in given path.
        ---
        parameters:
        - in: path
          name: path
          schema:
            type: string
          required: true
          description: the directory to create the resource at
        tags:
            - filesystem
        security:
            - BasicAuth: []
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        type: object
                        required: [files]
                        properties:
                            files:
                                type: array
                                items:
                                    type: file
                                    description: file to create
        responses:
            201:
                content:
                    application/json:
                        schema:
                            "$ref": "#/components/schemas/HttpResponse"

            400:
                $ref: "#/components/responses/BadRequest"
            401:
                $ref: "#/components/responses/Unauthorized"
            403:
                $ref: "#/components/responses/Forbidden"
            404:
                $ref: "#/components/responses/NotFound"
        """
        path = utils.normpath(path)
        username = current_username
        fs = FilesystemSvc(username=username)
        files = request.files.to_dict(flat=False).get("files", [])
        if not files:
            utils.abort_with(code=400, message="missing files")

        try:
            fs.upload_files(path=path, files=files)
            return utils.http_response(201), 201
        except PermissionError as ex:
            utils.abort_with(code=403, message=str(ex))
        except FileNotFoundError as ex:
            utils.abort_with(code=404, message=str(ex))
        except Exception as ex:
            utils.abort_with(code=400, message=str(ex))

    @requires_auth(schemes=["basic"])
    def put(self, path):
        """
        Update files in given path.
        ---
        parameters:
        - in: path
          name: path
          schema:
            type: string
          required: true
          description: the directory to update the resource at
        tags:
            - filesystem
        security:
            - BasicAuth: []
        requestBody:
            content:
                multipart/form-data:
                    schema:
                        type: object
                        required: [files]
                        properties:
                            files:
                                type: array
                                items:
                                    type: file
                                    description: file to update
        responses:
            204:
                content:
                    application/json:
                        schema:
                            "$ref": "#/components/schemas/HttpResponse"

            400:
                $ref: "#/components/responses/BadRequest"
            401:
                $ref: "#/components/responses/Unauthorized"
            403:
                $ref: "#/components/responses/Forbidden"
            404:
                $ref: "#/components/responses/NotFound"
        """
        path = utils.normpath(path)
        username = current_username
        fs = FilesystemSvc(username=username)
        files = request.files.to_dict(flat=False).get("files", [])
        if not files:
            utils.abort_with(code=400, message="missing files")

        try:
            fs.upload_files(path=path, files=files, update=True)
            return utils.http_response(204), 204
        except PermissionError as ex:
            utils.abort_with(code=403, message=str(ex))
        except FileNotFoundError as ex:
            utils.abort_with(code=404, message=str(ex))
        except Exception as ex:
            utils.abort_with(code=400, message=str(ex))

    @requires_auth(schemes=["basic"])
    def delete(self, path):
        """
        Delete file in given path.
        ---
        parameters:
        - in: path
          name: path
          schema:
            type: string
          required: true
          description: the path of the file
        tags:
            - filesystem
        security:
            - BasicAuth: []
        responses:
            204:
                content:
                    application/json:
                        schema:
                            "$ref": "#/components/schemas/HttpResponse"

            400:
                $ref: "#/components/responses/BadRequest"
            401:
                $ref: "#/components/responses/Unauthorized"
            403:
                $ref: "#/components/responses/Forbidden"
            404:
                $ref: "#/components/responses/NotFound"
        """
        path = utils.normpath(path)
        username = current_username
        fs = FilesystemSvc(username=username)
        try:
            fs.delete_file(path=path)
            return utils.http_response(204), 204
        except PermissionError as ex:
            utils.abort_with(code=403, message=str(ex))
        except FileNotFoundError as ex:
            utils.abort_with(code=404, message=str(ex))
        except Exception as ex:
            utils.abort_with(code=400, message=str(ex))
