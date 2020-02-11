"""
This module is responsible for the database session and transaction scope.
"""
import logging

import sqlalchemy.exc
from decorator import decorator
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import scoped_session, sessionmaker

from transiter import models, config

logger = logging.getLogger(__name__)


def create_engine():
    """
    Create a SQL Alchemy engine using config.DatabaseConfig.

    :return: the engine
    """
    connection_url = URL(
        drivername=config.DB_DRIVER,
        username=config.DB_USERNAME,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_DATABASE,
    )
    return sqlalchemy.create_engine(
        connection_url,
        executemany_mode="batch",
        executemany_values_page_size=10000,
        executemany_batch_page_size=500,
    )


engine = None
session_factory = None
Session = None


def ensure_db_connection():
    """
    Ensure that the SQL Alchemy engine and session factory have been initialized.
    """
    global engine, session_factory, Session
    if engine is not None:
        return
    engine = create_engine()
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)


class OutsideUnitOfWorkError(Exception):
    pass


class NestedUnitOfWorkError(Exception):
    pass


def get_session():
    """
    Get the current session.

    :return: the session
    :raises OutsideUnitOfWorkError: if this method is called from outside a UOW
    """
    global Session
    if Session is None or not Session.registry.has():
        raise OutsideUnitOfWorkError
    return Session()


@decorator
def unit_of_work(func, *args, **kw):
    """
    Decorator that handles beginning and ending a unit of work.
    """
    global Session
    ensure_db_connection()
    if Session.registry.has():
        raise NestedUnitOfWorkError
    session = Session()
    try:
        result = func(*args, **kw)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        Session.remove()

    return result


def init_db():
    """
    Initialize the Transiter database.
    """
    global engine
    ensure_db_connection()
    models.Base.metadata.create_all(engine)


def rebuild_db():
    """
    Erase the Transiter schema if it exists and then rebuild it.
    """
    global engine
    ensure_db_connection()
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)


def generate_schema():
    def dump(sql, *args, **kwargs):
        sql_string = str(sql.compile(dialect=engine.dialect)).strip()

        print("{};\n\n".format(sql_string))

    engine = sqlalchemy.create_engine("postgresql://", strategy="mock", executor=dump)
    models.Base.metadata.create_all(engine, checkfirst=False)
