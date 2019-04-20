import logging
import traceback
import warnings
import typing

import sqlalchemy.exc
from decorator import decorator
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import scoped_session, sessionmaker

from transiter import models, config

warnings.simplefilter(action='ignore', category=SAWarning)
logger = logging.getLogger(__name__)


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


def _perform_outer_database_action(operation: str,
                                   silent=True):
    """
    database = db_connection_params._database
    db_connection_params._database = 'postgres'
    outer_engine = create_engine(db_connection_params)
    conn = outer_engine.connect()
    print('Database: {}'.format(database))
    try:
        conn.execute('commit')
        conn.execute('{} DATABASE {}'.format(operation, database))
    except sqlalchemy.exc.ProgrammingError:
        if not silent:
            raise
    finally:
        conn.close()
        db_connection_params._database = database
    """
    raise Exception('Why is this method being used?')


def drop_database(silent=True):
    _perform_outer_database_action('DROP', silent)


def create_database(silent=True):
    _perform_outer_database_action('CREATE', silent)


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


def close_db_connection():
    global engine, session_factory, Session
    Session.remove()
    engine = None
    session_factory = None
    Session = None


# TODO: fail hard if not in a UOW context
def get_session():
    global Session
    return Session()


# TODO: Need to this to allow nesting of read sessions
# TODO: Fail hard if a nested write session is attempted
@decorator
def unit_of_work(func, *args, **kw):
    global Session
    ensure_db_connection()
    # TODO: investigate autoflush=False
    session = Session()
    #logger.debug('Opened unit of work session {}'.format(session))
    try:
        result = func(*args, **kw)
        session.commit()
    except Exception:
        logger.warning('Encountered error; rolling back session!')
        logger.warning('Stack trace:\n' + str(traceback.format_exc()))
        session.rollback()
        raise
    finally:
        #logger.debug('Closing unit of work session {}'.format(session))
        Session.remove()

    return result


def create_tables():
    global engine
    ensure_db_connection()
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)


def rebuild_db():
    create_tables()
