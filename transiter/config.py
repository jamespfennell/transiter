"""
The config module is responsible for loading Transiter's global config at
runtime and providing it to modules that require it.
"""
import logging
import os

from distutils.util import strtobool

logger = logging.getLogger(__name__)


DB_DRIVER = "postgresql"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_DATABASE = "transiter"
DB_USERNAME = "transiter"
DB_PASSWORD = "transiter"


SCHEDULER_HOST = "localhost"
SCHEDULER_PORT = "5000"

DOCUMENTATION_ENABLED = False
DOCUMENTATION_ROOT = "../../docs/site"


for env_variable_name, value in os.environ.items():
    prefix = "TRANSITER_"
    if env_variable_name[: len(prefix)] != prefix:
        continue
    variable_name = env_variable_name[len(prefix) :]
    if variable_name not in globals():
        logger.debug(
            "Skipping unknown Transiter environment setting '{}'.".format(variable_name)
        )
        continue
    if isinstance(globals()[variable_name], bool):
        value = bool(strtobool(value))
    logger.debug(
        "Setting Transiter environment variable '{}' to be '{}'.".format(
            variable_name, value
        )
    )
    globals()[variable_name] = value
