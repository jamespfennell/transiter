"""
The config module is responsible for loading Transiter's global config at
runtime and providing it to modules that require it.
"""

import os


DB_DRIVER = "postgresql"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_DATABASE = "transiter"
DB_USERNAME = "transiter"
DB_PASSWORD = "transiter"


TASKSERVER_HOST = "localhost"
TASKSERVER_PORT = "5000"


for env_variable_name, value in os.environ.items():
    prefix = "TRANSITER_"
    if env_variable_name[: len(prefix)] != prefix:
        continue
    variable_name = env_variable_name[len(prefix) :]
    if variable_name not in globals():
        continue
    globals()[variable_name] = value
