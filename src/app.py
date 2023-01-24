from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_plugins.types import AuthSchemes, Server, Tag
from apispec_plugins.utils import base_template
from apispec_plugins.webframeworks.flask import FlaskPlugin
from apispec_ui.flask import Swagger
from flask import Blueprint, Flask
from flask_cors import CORS

from src import __meta__, __version__
from src.api.filemgr import blueprint as fm
from src.api.filesystem import blueprint as fs
from src.settings import oas
from src.settings.ctx import ctx_settings
from src.settings.env import config_class


def create_app(environ="development", configs=None):
    """Create a new app."""

    # define the WSGI application object
    app = Flask(__name__, static_folder=None)

    # load object-based default configuration
    app.config.from_object(config_class(environ))
    app.config.update(configs or {})

    setup_app(app)

    return app


def setup_app(app):
    """Initial setups."""
    CORS(app)  # enable CORS

    url_prefix = app.config["APPLICATION_ROOT"]
    openapi_version = app.config["OPENAPI"]

    # initial blueprint wiring
    index = Blueprint("index", __name__)
    index.register_blueprint(fs)
    index.register_blueprint(fm)
    app.register_blueprint(index, url_prefix=url_prefix)

    spec_template = base_template(
        openapi_version=openapi_version,
        info={
            "title": __meta__["name"],
            "version": __version__,
            "description": __meta__["summary"],
        },
        servers=[Server(url=url_prefix, description=app.config["ENV"])],
        auths=[AuthSchemes.BasicAuth()],
        tags=[
            Tag(
                name="filesystem",
                description="CRUD operations over files in the current filesystem",
            ),
            Tag(
                name="file manager",
                description="Actions that serve React component named File Manager",
            ),
        ],
    )

    spec = APISpec(
        title=__meta__["name"],
        version=__version__,
        openapi_version=openapi_version,
        plugins=(FlaskPlugin(), MarshmallowPlugin()),
        **spec_template
    )

    # create paths from app views
    for view in app.view_functions.values():
        spec.path(view=view, app=app, base_path=url_prefix)

    # create views for Swagger
    Swagger(app=app, apispec=spec, config=oas.swagger_configs(app_root=url_prefix))

    # settings within app ctx
    ctx_settings(app)
