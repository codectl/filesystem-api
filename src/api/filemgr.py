import json
import os

from flask import Blueprint, jsonify, request, send_file
from flask_restful import Api, Resource
from http.client import HTTPException
from werkzeug.utils import secure_filename

from src import utils
from src.api.auth import current_username, requires_auth
from src.services.file_manager import FileManagerSvc
from src.schemas.serlializers.responses import FileManagerDataSchema

blueprint = Blueprint("file_manager", __name__, url_prefix="/file-manager")
api = Api(blueprint)


@api.resource("/actions", endpoint="fm_actions")
class FileManagerActions(Resource):
    def post(self):
        """
        Use request body to specify intended action on given path.
        ---
        tags:
            - File Manager
        responses:
            200:
                content:
                    application/json:
                        schema:
                            oneOf:
                                - FileManagerDataSchema
        """
        body = request.json
        svc = FileManagerSvc(username=None)
        try:
            if body["action"] in ["read", "search"]:
                files = svc.list_files(
                    path=body["path"],
                    substr=body.get("searchString"),
                    show_hidden=bool(body["showHiddenItems"]),
                )
                return {
                    "cwd": svc.stats(path=body["path"]),
                    "files": [svc.stats(file) for file in files],
                }
            elif body["action"] == "details":
                stats = []
                for data in body["data"]:
                    file_stats = svc.stats(data["path"])
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
                svc.create_dir(path=body["path"], name=body["name"])
                return {
                    "files": [svc.stats(os.path.join(body["path"], body["name"]))],
                }
            elif body["action"] == "delete":
                for name in body["names"]:
                    path = os.path.join(body["path"], name)
                    svc.remove_path(path=path)
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
                if svc.exists_path(dst):
                    return {
                        "error": {
                            "code": "400",
                            "message": f"Cannot rename {body['name']} to {body['newName']}: "
                                       f"destination already exists.",
                        }
                    }
                else:
                    svc.rename_path(src=src, dst=dst)
                    return {
                        "files": [
                            svc.stats(os.path.join(body["path"], body["newName"]))
                        ],
                    }
            elif body["action"] == "move":
                files = []
                conflicts = []
                for name in body["names"]:
                    src = body["path"]
                    dst = body["targetPath"]
                    if (
                            svc.exists_path(os.path.join(dst, name))
                            and name not in body["renameFiles"]
                    ):
                        conflicts.append(name)
                    else:
                        svc.move_path(src=os.path.join(src, name), dst=dst)
                        stats = svc.stats(os.path.join(dst, name))
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
                    svc.copy_path(src=os.path.join(src, name), dst=dst)
                    stats = svc.stats(os.path.join(dst, name))
                    files.append(stats)
                return {"files": files}
            else:
                raise ValueError

        except PermissionError:
            return {"error": {"code": 401, "message": "Permission Denied"}}
        except FileNotFoundError:
            return {"error": {"code": 404, "message": "File Not Found"}}
        except OSError:
            return {"error": {"code": 400, "message": "Bad request"}}


@api.resource("/download", endpoint="fm_download")
class FileManagerDownload(Resource):
    def post(self):
        body = json.loads(request.form["downloadInput"])
        svc = FileManagerSvc(username=None)
        data = body["data"]
        if len(data) == 1:
            obj = data[0]
            path = obj["path"]
            if os.path.isfile(path):
                return send_file(path, as_attachment=True)

        paths = (d["path"] for d in data)
        tarfile = svc.create_attachment(paths=paths)
        filename = f"{'files' if len(data) > 1 else data[0]['name']}.tar.gz"
        return send_file(
            tarfile,
            as_attachment=True,
            mimetype="application/gzip",
            download_name=filename,
        )


@api.resource("/upload", endpoint="fm_upload")
class FileManagerUpload(Resource):
    def post(self):
        body = request.form
        svc = FileManagerSvc(username=None)
        try:
            if body["action"] == "save":
                file = request.files["uploadFiles"]
                filename = secure_filename(file.filename)
                file.save(os.path.join(body["path"], filename))
            elif body["action"] == "remove":
                path = os.path.join(body["path"], body["cancel-uploading"])
                if svc.exists_path(path):
                    svc.remove_path(path)
            else:
                raise ValueError
            return utils.http_response(200), 200
        except OSError:
            return {"error": {"code": 400, "message": "Bad request"}}


@api.resource("/images", endpoint="fm_images")
class FileManagerImages(Resource):
    def get(self):
        path = os.path.join(os.path.sep, request.args.get("path", ""))
        svc = FileManagerSvc(username=None)
        try:
            if svc.exists_path(path):
                return send_file(path, mimetype="image/jpg")
            else:
                raise FileNotFoundError
        except PermissionError:
            return utils.abort_with(401)
        except FileNotFoundError:
            return utils.abort_with(404)
        except OSError:
            return utils.abort_with(400)
