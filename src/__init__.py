from importlib import metadata

__meta__ = metadata.metadata("filesystem-api")
__version__ = __meta__["version"]
