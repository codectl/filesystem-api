import operator as op
import os

from flask import Blueprint, jsonify, request, send_file
from flask_restful import Api, Resource
from http.client import HTTPException

from src import utils
from src.api.filesystem import FilesystemAPI
from src.resources.auth import current_username, requires_auth

blueprint = Blueprint("file_manager", __name__, url_prefix="/file-manager")
api = Api(blueprint)


@api.resource("/actions", endpoint="fm_actions")
class FileManagerActions(Resource):
    # @requires_auth(schemes=["basic"])
    def options(self):
        return utils.http_response(200), 200

    def post(self):
        """
        Use request body to specify intended action on given path.
        ---
        tags:
            - File Manager
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
                    file_stats = fs.stats(data["path"])
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
                    "files": [fs.stats(os.path.join(body["path"], body["name"]))],
                }
            elif body["action"] == "delete":
                for name in body["names"]:
                    path = os.path.join(body["path"], name)
                    fs.remove_path(path=path)
                return {
                    "path": body["path"],
                    "files": [
                        {"path": os.path.join(body["path"], name)}
                        for name in body["names"]
                    ],
                }
            elif body["action"] == "rename":
                src = os.path.join(body["path"], body["name"])
                dst = os.path.join(body["path"], body["newName"])
                if os.path.exists(dst):
                    return {
                        "error": {
                            "code": "400",
                            "message": f"Cannot rename {body['name']} to {body['newName']}: "
                            f"destination already exists.",
                        }
                    }
                else:
                    fs.rename_path(src=src, dst=dst)
                    return {
                        "files": [
                            fs.stats(os.path.join(body["path"], body["newName"]))
                        ],
                    }
            elif body["action"] == "move":
                files = []
                conflicts = []
                for name in body["names"]:
                    src = body["path"]
                    dst = body["targetPath"]
                    if (
                        os.path.exists(os.path.join(dst, name))
                        and name not in body["renameFiles"]
                    ):
                        conflicts.append(name)
                    else:
                        fs.move_path(src=os.path.join(src, name), dst=dst)
                        stats = fs.stats(os.path.join(dst, name))
                        files.append(stats)
                response = {"files": files}
                if conflicts:
                    response["error"] = {
                        "code": 400,
                        "message": "File Already Exists",
                        "fileExists": conflicts,
                    }
                return response
            elif body["action"] == "copy":
                files = []
                for name in body["names"]:
                    src = body["path"]
                    dst = body["targetPath"]
                    fs.copy_path(src=os.path.join(src, name), dst=dst)
                    stats = fs.stats(os.path.join(dst, name))
                    files.append(stats)
                return {"files": files}

        except PermissionError:
            return {"error": {"code": 401, "message": "Permission Denied"}}
        except FileNotFoundError:
            return {"error": {"code": 404, "message": "File Not Found"}}
        except Exception as ex:
            return {"error": {"code": 400, "message": "Bad request"}}


@api.resource("/download", endpoint="fm_download")
class FileManagerDownload(Resource):
    # @requires_auth(schemes=["basic"])
    def options(self):
        return utils.http_response(200), 200

    def post(self):
        pass
