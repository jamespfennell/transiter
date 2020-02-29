import time

import pytest

from transiter.data import dbconnection

# noinspection PyUnresolvedReferences
from .data import *


@pytest.fixture(scope="session")
def test_db():
    for __ in range(100):
        try:
            dbconnection.rebuild_db()
            return
        except Exception as e:
            print("Could not initialize DB, trying again soon. Reason: ", e)
            time.sleep(0.1)
    raise Exception("Could not initialize the DB after 10 seconds!")


@pytest.fixture
def db_session(test_db):
    with dbconnection.inline_unit_of_work() as session:
        yield session
        session.rollback()


@pytest.fixture
def add_model(db_session):
    def add(model):
        db_session.add(model)
        db_session.flush()
        return model

    return add
