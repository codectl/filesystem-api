import json
import os

from flask import Blueprint, jsonify, request, send_file
from flask_restful import Api, Resource
from http.client import HTTPException
from marshmallow import EXCLUDE
from werkzeug.utils import secure_filename

from src import utils
from src.api.auth import current_username, requires_auth
from src.schemas.deserializers import filemgr as dsl
from src.schemas.serlializers import filemgr as sl
from src.services.file_manager import FileManagerSvc

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
                                - FileMgrStatsSchema
                                - FileMgrErrorSchema
        """
        payload = request.json
        base_schema = dsl.BaseActionSchema
        dump_error = sl.ErrorSchema().dump
        dump_response = sl.ResponseSchema().dump

        errors = base_schema(only=("action",), unknown=EXCLUDE).validate(payload)
        if errors:
            return {"error": {"code": 400, "message": json.dumps(errors)}}

        svc = FileManagerSvc(username=None)

        try:
            if payload["action"] == "read":
                req = dsl.ReadActionSchema().load(payload)
                files = svc.list_files(
                    path=req["path"],
                    show_hidden=req["showHiddenItems"],
                )
                return dump_response(
                    {
                        "cwd": svc.stats(path=payload["path"]),
                        "files": [svc.stats(file) for file in files],
                    }
                )
            elif payload["action"] == "create":
                req = dsl.CreateActionSchema().load(payload)
                svc.create_dir(path=req["path"], name=req["name"])
                return dump_response(
                    {
                        "files": [svc.stats(os.path.join(req["path"], req["name"]))],
                    }
                )
            elif payload["action"] == "delete":
                req = dsl.DeleteActionSchema().load(payload)
                for name in req["names"]:
                    path = os.path.join(req["path"], name)
                    svc.remove_path(path=path)
                return dump_response(
                    {
                        "files": [
                            {"path": os.path.join(payload["path"], name)}
                            for name in payload["names"]
                        ],
                    }
                )
            elif payload["action"] == "rename":
                req = dsl.RenameActionSchema().load(payload)
                src = os.path.join(req["path"], req["name"])
                dst = os.path.join(req["path"], req["newName"])
                if svc.exists_path(dst):
                    return dump_error(
                        {
                            "error": {
                                "code": 400,
                                "message": f"Cannot rename {req['name']} to "
                                f"{req['newName']}: destination already exists.",
                            }
                        }
                    )
                else:
                    svc.rename_path(src=src, dst=dst)
                    return dump_response(
                        {
                            "files": [
                                svc.stats(os.path.join(req["path"], req["newName"]))
                            ],
                        }
                    )
            elif payload["action"] == "search":
                req = dsl.SearchActionSchema().load(payload)
                files = svc.list_files(
                    path=req["path"],
                    substr=req["searchString"],
                    show_hidden=req["showHiddenItems"],
                )
                return dump_response(
                    {
                        "cwd": svc.stats(path=req["path"]),
                        "files": [svc.stats(file) for file in files],
                    }
                )
            elif payload["action"] == "details":
                req = dsl.DetailsActionSchema().load(payload)
                stats = []
                for data in req["data"]:
                    file_stats = svc.stats(data["path"])
                    stats.append(file_stats)

                if not stats:
                    raise ValueError("Missing data")
                elif len(stats) == 1:
                    stats = stats[0]
                    return {
                        "details": sl.DetailsSchema().dump(
                            {
                                "name": stats["name"],
                                "size": utils.convert_bytes(stats["size"]),
                                "location": stats["path"],
                                "created": stats["dateCreated"],
                                "modified": stats["dateModified"],
                                "isFile": stats["isFile"],
                                "multipleFiles": False,
                            }
                        )
                    }
                elif len(stats) > 1:
                    size = sum(s["size"] for s in stats)
                    return {
                        "details": sl.DetailsSchema().dump(
                            {
                                "location": f"All in {os.path.dirname(stats[0]['path'])}",
                                "name": ", ".join(s["name"] for s in stats),
                                "size": utils.convert_bytes(size),
                                "isFile": False,
                                "multipleFiles": True,
                            }
                        )
                    }
            elif payload["action"] == "copy":
                req = dsl.SearchActionSchema().load(payload)
                files = []
                for name in req["names"]:
                    src = req["path"]
                    dst = req["targetPath"]
                    svc.copy_path(src=os.path.join(src, name), dst=dst)
                    stats = svc.stats(os.path.join(dst, name))
                    files.append(stats)
                return dump_response({"files": files})
            elif payload["action"] == "move":
                req = dsl.SearchActionSchema().load(payload)
                files = []
                conflicts = []
                for name in req["names"]:
                    src = req["path"]
                    dst = req["targetPath"]
                    if (
                        svc.exists_path(os.path.join(dst, name))
                        and name not in req["renameFiles"]
                    ):
                        conflicts.append(name)
                    else:
                        svc.move_path(src=os.path.join(src, name), dst=dst)
                        stats = svc.stats(os.path.join(dst, name))
                        files.append(stats)
                if conflicts:
                    return dump_error(
                        {
                            "code": 400,
                            "message": "File Already Exists",
                            "fileExists": conflicts,
                        }
                    )
                return dump_response({"files": files})
            else:
                raise ValueError

        except PermissionError:
            return dump_error({"error": {"code": 401, "message": "Permission Denied"}})
        except FileNotFoundError:
            return dump_error({"error": {"code": 404, "message": "File Not Found"}})
        except OSError:
            return dump_error({"error": {"code": 400, "message": "Bad request"}})


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
        payload = request.form
        dump_error = sl.ErrorSchema().dump
        svc = FileManagerSvc(username=None)
        try:
            if payload["action"] == "save":
                file = request.files["uploadFiles"]
                filename = secure_filename(file.filename)
                file.save(os.path.join(payload["path"], filename))
            elif payload["action"] == "remove":
                path = os.path.join(payload["path"], payload["cancel-uploading"])
                if svc.exists_path(path):
                    svc.remove_path(path)
            else:
                raise ValueError
            return utils.http_response(200), 200
        except OSError:
            return dump_error({"error": {"code": 400, "message": "Bad request"}})


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
