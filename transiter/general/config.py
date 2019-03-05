import os
import toml
from transiter.general import exceptions


DEFAULT_FILE_PATH = 'transiter-config.toml'


class _Config:
    def __init__(self):
        pass


class _DatabaseConfig(_Config):
    driver = 'sqlite'
    dialect = ''
    name = 'transiter.db'
    username = ''
    password = ''
    host = ''
    port = ''


class _TaskServerConfig(_Config):
    port = 5001


database = _DatabaseConfig()
taskserver = _TaskServerConfig()

_section_names = ['database', 'taskserver']

_toml_str = """
# Transiter configuration file

[database]

# The driver and dialect settings are used to specify which DBMS is in use
# and which Python package to use to connect to it. Currently officially 
# supported options:
#
# | DBMS       | Driver     | Dialect    | Additional python packages required |
# |------------+------------+------------+-------------------------------------|
# | SQLite     | sqlite     |            |                                     |
# | Postgresql | postgresql | psycopg2   | psycopg2-binary                     |

driver = '{database_driver}'
dialect = '{database_dialect}'

# The database name. Note that for SQLite the database name is the location 
# of the file on disk relative to the directory Transiter servers are launched.

name = '{database_name}'

# User settings.

username = '{database_username}'
password = '{database_password}'

# Host settings. If using Postgres or another client/server DBMS the database
# can be on a separate machine to the Transiter instance. If running the
# Transiter instance on the same Unix machine as the database, it is highly 
# recommended to use Unix domain sockets instead of TCP, in which case the
# host and port settings should be empty

host = '{database_host}'
port = '{database_port}'

[taskserver]

# The port that the task server listens on. This is used both when 
# launching the task server, and when the main HTTP server attempts to 
# communicate with it.

port = {taskserver_port:d}

"""
# TODO: add logging config


def _list_settings(default_values=True):
    """
    Return an iterator of three tuples (section name, setting name, value)
    for each setting.
    """
    global _toml_str, _section_names
    for section_name in _section_names:
        config_section = globals()[ section_name]
        if default_values:
            config_section = config_section.__class__()
        for setting in dir(config_section):
            if setting[0] == '_':
                continue
            yield section_name, setting, getattr(config_section, setting)


def _set_setting(section_name, setting_name, value):
    globals()[section_name].__setattr__(setting_name, value)


def load(file_path=None):
    file_must_exist = True
    if file_path is None:
        file_path = os.environ.get('TRANSITER_CONFIG', None)
        if file_path is None:
            file_must_exist = False
            file_path = DEFAULT_FILE_PATH

    try:
        with open(file_path, 'r') as file_handle:
            toml_str = file_handle.read()
    except FileNotFoundError:
        if file_must_exist:
            raise exceptions.ConfigFileNotFoundError()
        else:
            return

    new_config = toml.loads(toml_str)
    for section_name, setting_name, __ in _list_settings():
        new_value = new_config.get(section_name, {}).get(setting_name, None)
        if new_value is None:
            continue
        _set_setting(section_name, setting_name, new_value)


def generate(default_values=True):
    global _toml_str
    format_dict = {}
    for section_name, setting_name, value in _list_settings(
            default_values=default_values):
        format_dict[
            '{}_{}'.format(section_name, setting_name)
        ] = value
    return _toml_str.format(**format_dict)


load()
