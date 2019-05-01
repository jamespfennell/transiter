import logging
import traceback
import warnings
import typing

import sqlalchemy.exc
from decorator import decorator
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import scoped_session, sessionmaker

from transiter import models, config

#
# warnings.simplefilter(action='ignore', category=SAWarning)
logger = logging.getLogger(__name__)


# TODO: this is reinventing the wheel
# https://docs.sqlalchemy.org/en/13/core/engines.html#sqlalchemy.engine.url.make_url
def build_connection_url_from_config(database_config: typing.Type[config.DatabaseConfig]):
    pieces = ['']*9
    pieces[0] = database_config.DRIVER
    if database_config.DIALECT != '':
        pieces[1] = '+' + database_config.DIALECT
    pieces[2] = '://'
    if database_config.USERNAME != '':
        pieces[3] = database_config.USERNAME
        if database_config.PASSWORD != '':
            # TODO: does need to be encoded?
            pieces[4] = database_config.PASSWORD
        pieces[4] = '@'
    if database_config.HOST != '':
        pieces[5] = database_config.HOST
        if database_config.PORT != '':
            pieces[6] = ':' + database_config.PORT
    pieces[7] = '/'
    pieces[8] = database_config.NAME
    logger.info('Connection URL: ' + ''.join(pieces))
    return ''.join(pieces)


def build_extra_engine_params_from_config(database_config: typing.Type[config.DatabaseConfig]):
    extra_params = {}
    if database_config.DRIVER == 'postgresql':
        if database_config.DIALECT == '' or database_config.DIALECT == 'psycopg2':
            extra_params['use_batch_mode'] = True
    logger.info('Extra connection params: ' + str(extra_params))
    return extra_params


def create_engine():
    connection_url = build_connection_url_from_config(config.DatabaseConfig)
    extra_params = build_extra_engine_params_from_config(config.DatabaseConfig)
    return sqlalchemy.create_engine(connection_url, **extra_params)



engine = None
session_factory = None
Session = None


def ensure_db_connection():
    global engine, session_factory, Session
    if engine is not None:
        return
    engine = create_engine()
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)


# TODO: fail hard if not in a UOW context
# TODO Leave note explaining why this is thread safe
def get_session():
    global Session
    return Session()


# TODO: Fail hard if a nested write session is attempted
@decorator
def unit_of_work(func, *args, **kw):
    global Session
    ensure_db_connection()
    session = Session()
    try:
        result = func(*args, **kw)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return result


def rebuild_db():
    global engine
    ensure_db_connection()
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)

