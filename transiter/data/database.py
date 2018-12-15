from decorator import decorator
import os
import sqlalchemy.exc
from sqlalchemy.orm import scoped_session, sessionmaker

from transiter import models


class DatabaseConnectionParameters:

    def __init__(self, database, user, password=None):
        self._database = database
        self._user = user
        self._password = password
        self._driver = 'postgresql'
        self._dialect = None
        self._host = None
        self._port = None

    def set_driver(self, driver, dialect=None):
        self._driver = driver
        self._dialect = dialect

    def set_host(self, host, port=None):
        self._host = host
        self._port = port

    def create_url(self):
        pieces = ['']*9
        pieces[0] = self._driver
        if self._dialect is not None:
            pieces[1] = '+' + str(self._dialect)
        pieces[2] = '://'
        pieces[3] = self._user
        if self._password is not None:
            pieces[4] = self._password
        pieces[4] = '@'
        if self._host is not None:
            pieces[5] = self._host
            if self._port is not None:
                pieces[6] = ':' + str(self._port)
        pieces[7] = '/'
        pieces[8] = self._database
        return ''.join(pieces)


def create_engine(actual_db_connection_params: DatabaseConnectionParameters):
    return sqlalchemy.create_engine(actual_db_connection_params.create_url())


def _perform_outer_database_action(operation: str,
                                   silent=True):
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


def drop_database(silent=True):
    _perform_outer_database_action('DROP', silent)


def create_database(silent=True):
    _perform_outer_database_action('CREATE', silent)


# TODO allow way to specify full config and load at this point
db_name = os.environ.get('TRANSITER_DB_NAME', 'realtimerail')
db_user = os.environ.get('TRANSITER_DB_USER', 'james')
db_connection_params = DatabaseConnectionParameters(db_name, db_user)
engine = None
session_factory = None
Session = None


def ensure_db_connection():
    global engine, session_factory, Session
    if engine is not None:
        return
    engine = create_engine(db_connection_params)
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
    session = Session()
    try:
        result = func(*args, **kw)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        Session.remove()

    return result


def create_tables():
    global engine
    ensure_db_connection()
    models.Base.metadata.create_all(engine)


