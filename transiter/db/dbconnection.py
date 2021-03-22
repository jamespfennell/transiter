"""
This module is responsible for the database session and transaction scope.
"""
import logging
from contextlib import contextmanager

import sqlalchemy.exc
from alembic import command
from alembic.config import Config
from decorator import decorator
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import scoped_session, sessionmaker

from transiter import config
from transiter.db import models

logger = logging.getLogger(__name__)


def create_engine():
    """
    Create a SQL Alchemy engine using config.DatabaseConfig.

    :return: the engine
    """
    connection_url = URL.create(
        drivername=config.DB_DRIVER,
        username=config.DB_USERNAME,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_DATABASE,
    )
    return sqlalchemy.create_engine(
        connection_url,
        executemany_mode="values",
        executemany_values_page_size=1000,
        executemany_batch_page_size=200,
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
    session_factory = sessionmaker(bind=engine, future=True)
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


@contextmanager
def inline_unit_of_work():
    """
    Context manager that handles beginning and ending a unit of work.
    """
    global Session
    ensure_db_connection()
    if Session.registry.has():
        raise NestedUnitOfWorkError
    session = Session()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        Session.remove()


@decorator
def unit_of_work(func, *args, **kw):
    """
    Decorator that handles beginning and ending a unit of work.
    """
    with inline_unit_of_work():
        return func(*args, **kw)


def delete_all_tables():
    """
    Delete all Transiter tables in the database.
    """
    global engine
    ensure_db_connection()
    models.Base.metadata.drop_all(engine)
    alembic_config = _get_alembic_config()
    command.stamp(alembic_config, None)


def upgrade_database():
    command.upgrade(_get_alembic_config(), "head")


def get_current_database_revision():
    captured_text = None

    def print_stdout(text, *arg, **kwargs):
        nonlocal captured_text
        captured_text = text

    alembic_config = _get_alembic_config()
    alembic_config.print_stdout = print_stdout
    command.current(alembic_config)
    return captured_text


def _get_alembic_config() -> Config:
    alembic_config = Config()
    alembic_config.set_main_option("script_location", "transiter.db:alembic")
    return alembic_config
