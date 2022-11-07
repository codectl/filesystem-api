import environs


def config_class(environment: str):
    """Link given environment to a config class."""
    return f"{__package__}.config.{environment.capitalize()}Config"


# the application environment
env = environs.Env()
env.read_env(".env")
