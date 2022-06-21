import operator as op
import os

from flask import Blueprint, jsonify, request, send_file
from flask_restful import Api, Resource
from http.client import HTTPException

from src import utils
from src.api.filesystem import FilesystemAPI
from src.resources.auth import current_username, requires_auth

blueprint = Blueprint("filesystem", __name__)
api = Api(blueprint)


@api.resource("/<path:path>", endpoint="fs")
class Filesystem(Resource):
    @requires_auth(schemes=["basic"])
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
        fs_api = FilesystemAPI(username=username)
        try:
            accept = request.headers.get("accept", "application/json")
            if accept == "application/json":
                return jsonify(fs_api.list_files(path=path))
            elif accept == "application/octet-stream":
                stats = fs_api.list_files(path=path, flags="-dlL")[0]
                mode = utils.file_mode(stats=stats)
                name, content = fs_api.attachment(path=path, mode=mode)
                return send_file(content, attachment_filename=name, as_attachment=True)
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
        fs = FilesystemAPI(username=username)
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
        fs = FilesystemAPI(username=username)
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
        fs = FilesystemAPI(username=username)
        try:
            fs.delete_file(path=path)
            return utils.http_response(204), 204
        except PermissionError as ex:
            utils.abort_with(code=403, message=str(ex))
        except FileNotFoundError as ex:
            utils.abort_with(code=404, message=str(ex))
        except Exception as ex:
            utils.abort_with(code=400, message=str(ex))


@api.resource("/actions", endpoint="actions")
class FilesystemActions(Resource):
    # @requires_auth(schemes=["basic"])
    def options(self):
        return utils.http_response(200), 200

    def post(self):
        """
        Use request body to specify intended action on given path.
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
        body = request.json
        fs = FilesystemAPI(username=None)
        try:
            if body["action"] in ["read", "search"]:
                files = fs.list_files(
                    path=body["path"],
                    substr=body.get("searchString"),
                    show_hidden=bool(body["showHiddenItems"]),
                )
                return {
                    "cwd": fs.stats(path=body["path"]),
                    "files": [fs.stats(file) for file in files],
                }
            elif body["action"] == "details":
                stats = []
                for data in body["data"]:
                    file_stats = fs.stats(os.path.join(body["path"], data["name"]))
                    stats.append(file_stats)

                response = {}
                if not stats:
                    raise ValueError("Missing data")
                elif len(stats) == 1:
                    stats = stats[0]
                    response["name"] = stats["name"]
                    response["size"] = utils.convert_bytes(stats["size"])
                    response["location"] = stats["path"]
                    response["created"] = stats["dateCreated"]
                    response["modified"] = stats["dateModified"]
                    response["isFile"] = stats["isFile"]
                    response["multipleFiles"] = False
                elif len(stats) > 1:
                    size = sum(s["size"] for s in stats)
                    location = f"All in {os.path.dirname(stats[0]['path'])}"
                    response["name"] = ", ".join(s["name"] for s in stats)
                    response["size"] = utils.convert_bytes(size)
                    response["location"] = location
                    response["isFile"] = False
                    response["multipleFiles"] = True
                return {"details": response}
            elif body["action"] == "create":
                fs.create_dir(path=body["path"], name=body["name"])
                return {
                    "path": body["path"],
                    "name": body["name"],
                    "files": [fs.stats(os.path.join(body["path"], body["name"]))],
                }
            elif body["action"] == "delete":
                for name in body["names"]:
                    path = os.path.join(body["path"], name)
                    fs.remove_path(path=path)
                return {
                    "path": body["path"],
                    "names": body["names"],
                    "files": [
                        {"path": os.path.join(body["path"], name)}
                        for name in body["names"]
                    ],
                }
            elif body["action"] == "rename":
                fs.rename(
                    path=body["path"], old_name=body["name"], new_name=body["newName"]
                )
                return {
                    "path": body["path"],
                    "name": body["name"],
                    "files": [fs.stats(os.path.join(body["path"], body["newName"]))],
                }

        except PermissionError:
            return {"error": {"code": 401, "message": "Permission denied"}}
        except FileNotFoundError:
            return {"error": {"code": 404, "message": "File not found"}}
        except FileExistsError:
            return {
                "error": {
                    "code": 400,
                    "message": f"File \"{body['name']}\" already exists in \""
                    f"{body['path']}\".",
                }
            }
        # except Exception as ex:
        #     return {"error": {"code": 400, "message": "Bad request"}}
