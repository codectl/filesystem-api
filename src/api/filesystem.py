import os

from flask import Blueprint, request, send_file
from flask_restful import Api, Resource
from http.client import HTTPException

from src import utils
from src.services.filesystem import FilesystemSvc
from src.api.auth import current_username, requires_auth

blueprint = Blueprint("filesystem", __name__)
api = Api(blueprint)


@api.resource("/<path:path>", endpoint="fs")
class Filesystem(Resource):
    @requires_auth(schemes=["basic"])
    def get(self, path):
        """
        List files in given path.
        ---
        tags:
            - filesystem
        security:
            - BasicAuth: []
        parameters:
            - in: path
              name: path
              schema:
                type: string
              required: true
              description: the path to list content from
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
        svc = FilesystemSvc(username=current_username)
        try:
            accept = request.headers.get("accept", "application/json")
            if accept == "application/json":
                return [file.name for file in svc.list(path=path)]
            elif accept == "application/octet-stream":
                if svc.is_file(path):  # check for regular file
                    return send_file(path, as_attachment=True)
                else:
                    tarfile = svc.create_attachment(paths=(path,))
                    return send_file(
                        tarfile,
                        as_attachment=True,
                        mimetype="application/gzip",
                        download_name=f"{path.name}.tar.gz",
                    )
            raise HTTPException("unsupported 'accept' HTTP header")

        except PermissionError as ex:
            utils.abort_with(code=403, message=str(ex))
        except FileNotFoundError as ex:
            utils.abort_with(code=404, message=str(ex))
        except HTTPException as ex:
            utils.abort_with(code=400, message=str(ex))

    @requires_auth(schemes=["basic"])
    def post(self, path):
        """
        Create files in given path.
        ---
        tags:
            - filesystem
        security:
            - BasicAuth: []
        parameters:
            - in: path
              name: path
              schema:
                type: string
              required: true
              description: the directory to create the resource at
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
        """
        path = utils.normpath(path)
        username = current_username
        svc = FilesystemSvc(username=username)
        files = request.files.to_dict(flat=False).get("files", [])
        if not files:
            utils.abort_with(code=400, message="missing files")
        try:
            if any(svc.exists(os.path.join(path, file.filename)) for file in files):
                raise FileExistsError("a file already exists in given path")
            for file in files:
                svc.save(path, file=file)
            return utils.http_response(201), 201
        except PermissionError as ex:
            utils.abort_with(code=403, message=str(ex))
        except (FileNotFoundError, FileExistsError) as ex:
            utils.abort_with(code=400, message=str(ex))

    @requires_auth(schemes=["basic"])
    def put(self, path):
        """
        Update files in given path.
        ---
        tags:
            - filesystem
        security:
            - BasicAuth: []
        parameters:
            - in: path
              name: path
              schema:
                type: string
              required: true
              description: the directory to update the resource at
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
                description: the resource was updated
            400:
                $ref: "#/components/responses/BadRequest"
            401:
                $ref: "#/components/responses/Unauthorized"
            403:
                $ref: "#/components/responses/Forbidden"
        """
        path = utils.normpath(path)
        svc = FilesystemSvc(username=current_username)
        files = request.files.to_dict(flat=False).get("files", [])

        if not files:
            utils.abort_with(code=400, message="missing files")
        try:
            if not all(svc.exists(os.path.join(path, file.filename)) for file in files):
                raise FileNotFoundError("a file does not exist in given path")
            for file in files:
                svc.save(path, file=file)
            return None, 204
        except PermissionError as ex:
            utils.abort_with(code=403, message=str(ex))
        except FileNotFoundError as ex:
            utils.abort_with(code=400, message=str(ex))

    @requires_auth(schemes=["basic"])
    def delete(self, path):
        """
        Delete file in given path.
        ---
        tags:
            - filesystem
        security:
            - BasicAuth: []
        parameters:
            - in: path
              name: path
              schema:
                type: string
              required: true
              description: the path of the file
        responses:
            204:
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/HttpResponse"

            400:
                $ref: "#/components/responses/BadRequest"
            401:
                $ref: "#/components/responses/Unauthorized"
            403:
                $ref: "#/components/responses/Forbidden"
        """
        path = utils.normpath(path)
        svc = FilesystemSvc(username=current_username)
        try:
            svc.delete(path=path)
            return utils.http_response(204), 204
        except PermissionError as ex:
            utils.abort_with(code=403, message=str(ex))
        except FileNotFoundError as ex:
            utils.abort_with(code=400, message=str(ex))
        except OSError as ex:
            utils.abort_with(code=400, message=str(ex))
