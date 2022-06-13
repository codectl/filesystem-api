from dataclasses import dataclass

from src.settings.env import env


@dataclass
class BaseConfig:
    """Base configurations."""

    DEBUG = False
    TESTING = False

    # application root context
    APPLICATION_ROOT = env.str("APPLICATION_ROOT", "/")

    # OPENAPI supported version
    OPENAPI = env.str("OPENAPI", "3.0.3")


@dataclass
class ProductionConfig(BaseConfig):
    ENV = "production"
    LOG_LEVEL = "INFO"


@dataclass
class DevelopmentConfig(BaseConfig):
    ENV = "development"
    DEBUG = True
    LOG_LEVEL = "DEBUG"


@dataclass
class TestingConfig(BaseConfig):
    ENV = "testing"
    TESTING = True
    LOG_LEVEL = "DEBUG"
