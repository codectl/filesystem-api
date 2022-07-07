import os

from flask import Blueprint, request, send_file
from flask_restful import Api, Resource
from marshmallow import EXCLUDE, ValidationError

from src import utils
from src.api.auth import current_username
from src.schemas.deserializers import filemgr as dsl
from src.schemas.serializers import filemgr as sl
from src.services.filemgr import FileManagerSvc

blueprint = Blueprint("file_manager", __name__, url_prefix="/file-manager")
api = Api(blueprint)


@api.resource("/actions", endpoint="fm_actions")
class FileManagerActions(Resource):
    def post(self):
        """
        Use request body to specify intended action on given path.
        ---
        tags:
            - file manager
        requestBody:
            description: action properties
            required: true
            content:
                application/json:
                    schema:
                        oneOf:
                            - ReadActionSchema
                            - CreateActionSchema
                            - DeleteActionSchema
                            - RenameActionSchema
                            - SearchActionSchema
                            - DetailsActionSchema
                            - CopyActionSchema
                            - MoveActionSchema
        responses:
            200:
                content:
                    application/json:
                        schema:
                            oneOf:
                                - StatsResponseSchema
                                - DetailsResponseSchema
                                - ErrorResponseSchema
        """
        payload = request.json
        svc = FileManagerSvc(username=current_username)
        try:
            # throw error when invalid action
            dsl.ReadActionSchema(only=("action",), unknown=EXCLUDE).load(payload)
            if payload["action"] == "read":
                req = dsl.ReadActionSchema().load(payload)
                files = svc.list_files(
                    path=req["path"],
                    show_hidden=req["showHiddenItems"],
                )
                return sl.dump_stats(
                    cwd=svc.stats(path=req["path"]),
                    files=[svc.stats(file.path) for file in files],
                )
            elif payload["action"] == "create":
                req = dsl.CreateActionSchema().load(payload)
                svc.make_dir(path=req["path"], name=req["name"])
                return sl.dump_stats(
                    files=[svc.stats(os.path.join(req["path"], req["name"]))],
                )
            elif payload["action"] == "delete":
                req = dsl.DeleteActionSchema().load(payload)
                for name in req["names"]:
                    path = os.path.join(req["path"], name)
                    svc.remove_path(path=path)
                return sl.dump_stats(
                    files=[
                        {"path": os.path.join(payload["path"], name)}
                        for name in payload["names"]
                    ],
                )
            elif payload["action"] == "rename":
                req = dsl.RenameActionSchema().load(payload)
                src = os.path.join(req["path"], req["name"])
                dst = os.path.join(req["path"], req["newName"])
                if svc.exists_path(dst):
                    return sl.dump_error(
                        code=400,
                        message=f"Cannot rename {req['name']} to "
                        f"{req['newName']}: destination already exists.",
                    )
                else:
                    svc.rename_path(src=src, dst=dst)
                    return sl.dump_stats(
                        files=[svc.stats(os.path.join(req["path"], req["newName"]))]
                    )
            elif payload["action"] == "search":
                req = dsl.SearchActionSchema().load(payload)
                files = svc.list_files(
                    path=req["path"],
                    substr=req["searchString"],
                    show_hidden=req["showHiddenItems"],
                )
                return sl.dump_stats(
                    cwd=svc.stats(path=req["path"]),
                    files=[svc.stats(file.path) for file in files],
                )
            elif payload["action"] == "details":
                req = dsl.DetailsActionSchema().load(payload)
                stats = []
                for name in req["names"]:
                    path = os.path.join(req["path"], name)
                    file_stats = svc.stats(path=path)
                    stats.append(file_stats)

                if not stats:
                    raise ValueError("Missing data")
                elif len(stats) == 1:
                    stats = stats[0]
                    return sl.dump_details(
                        name=stats["name"],
                        size=utils.convert_bytes(stats["size"]),
                        location=stats["path"],
                        created=stats["dateCreated"],
                        modified=stats["dateModified"],
                        isFile=stats["isFile"],
                        multipleFiles=False,
                    )
                elif len(stats) > 1:
                    size = sum(s["size"] for s in stats)
                    return sl.dump_details(
                        location=f"All in {os.path.dirname(stats[0]['path'])}",
                        name=", ".join(s["name"] for s in stats),
                        size=utils.convert_bytes(size),
                        isFile=False,
                        multipleFiles=True,
                    )
            elif payload["action"] == "copy":
                req = dsl.CopyActionSchema().load(payload)
                files = []
                for name in req["names"]:
                    src = req["path"]
                    dst = req["targetPath"]
                    path = svc.copy_path(src=os.path.join(src, name), dst=dst)
                    stats = svc.stats(path)
                    files.append(stats)
                return sl.dump_stats(files=files)
            elif payload["action"] == "move":
                req = dsl.MoveActionSchema().load(payload)
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
                        path = svc.move_path(src=os.path.join(src, name), dst=dst)
                        stats = svc.stats(path)
                        files.append(stats)
                if conflicts:
                    return sl.dump_error(
                        code=400,
                        message="File Already Exists",
                        fileExists=conflicts,
                        files=files,
                    )
                return sl.dump_stats(files=files)

        except PermissionError:
            return sl.dump_error(code=403, message="Permission Denied")
        except FileNotFoundError:
            return sl.dump_error(code=404, message="File Not Found")
        except (OSError, ValidationError):
            return sl.dump_error(code=400, message="Bad request")


@api.resource("/download", endpoint="fm_download")
class FileManagerDownload(Resource):
    def post(self):
        """
        Download files. Multiple files are merged into a zipped file.
        ---
        tags:
            - file manager
        requestBody:
            description: action properties
            required: true
            content:
                application/x-www-form-urlencoded:
                    schema: DownloadSchema
        responses:
            200:
                content:
                    application/*:
                        schema:
                            type: string
                            format: binary
            400:
                $ref: "#/components/responses/BadRequest"
            401:
                $ref: "#/components/responses/Unauthorized"
            403:
                $ref: "#/components/responses/Forbidden"
        """
        payload = request.form
        svc = FileManagerSvc(username=current_username)
        try:
            req = dsl.DownloadSchema().load(payload)
            names = req["downloadInput"]["names"]
            paths = [os.path.join(req["downloadInput"]["path"], name) for name in names]
            if len(paths) == 1:
                path = paths[0]
                if svc.isfile(path):
                    return send_file(path, as_attachment=True)

            tarfile = svc.create_attachment(paths=paths)
            filename = f"{'files' if len(names) > 1 else names[0]}.tar.gz"
            return send_file(
                tarfile,
                as_attachment=True,
                mimetype="application/gzip",
                download_name=filename,
            )
        except PermissionError:
            utils.abort_with(403)
        except FileNotFoundError:
            utils.abort_with(404)
        except (OSError, ValidationError):
            utils.abort_with(400)


@api.resource("/upload", endpoint="fm_upload")
class FileManagerUpload(Resource):
    def post(self):
        """
        Upload files.
        ---
        tags:
            - file manager
        requestBody:
            description: action properties
            required: true
            content:
                multipart/form-data:
                    schema: UploadSchema
        responses:
            200:
                content:
                    application/json:
                        schema:
                            oneOf:
                                - $ref: "#/components/schemas/HttpResponse"
                                - ErrorResponseSchema
            400:
                $ref: "#/components/responses/BadRequest"
            401:
                $ref: "#/components/responses/Unauthorized"
            403:
                $ref: "#/components/responses/Forbidden"
        """
        payload = request.form
        svc = FileManagerSvc(username=current_username)
        try:
            req = dsl.UploadSchema().load(payload)
            if req["action"] == "save":
                file = request.files["uploadFiles"]
                svc.save_file(req["path"], file=file)
            elif req["action"] == "remove":
                path = os.path.join(req["path"], req["cancel-uploading"])
                if svc.exists_path(path):
                    svc.remove_path(path)
            return utils.http_response(200), 200
        except PermissionError:
            utils.abort_with(403)
        except FileNotFoundError:
            utils.abort_with(404)
        except (OSError, ValidationError):
            utils.abort_with(400)


@api.resource("/images", endpoint="fm_images")
class FileManagerImages(Resource):
    def get(self):
        """
        Get images.
        ---
        tags:
            - file manager
        parameters:
            - in: query
              name: path
              schema:
                type: string
              description: the filesystem path
        responses:
            200:
                content:
                    image/*:
                        schema:
                            type: string
                            format: binary
            400:
                $ref: "#/components/responses/BadRequest"
            403:
                $ref: "#/components/responses/Forbidden"
            404:
                $ref: "#/components/responses/NotFound"
        """
        path = os.path.join(os.path.sep, request.args.get("path", ""))
        svc = FileManagerSvc(username=current_username)
        try:
            if not svc.exists_path(path):
                raise FileNotFoundError
            return send_file(path)
        except PermissionError:
            utils.abort_with(403)
        except FileNotFoundError:
            utils.abort_with(404)
