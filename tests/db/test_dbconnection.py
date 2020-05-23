import pytest

from transiter.db import dbconnection


def test_outside_unit_of_work_error__before():
    with pytest.raises(dbconnection.OutsideUnitOfWorkError):
        dbconnection.get_session()


def test_outside_unit_of_work_error__after():
    @dbconnection.unit_of_work
    def uow():
        return 1 + 1

    uow()

    with pytest.raises(dbconnection.OutsideUnitOfWorkError):
        dbconnection.get_session()


def test_nested_unit_of_work_error():
    @dbconnection.unit_of_work
    def uow_1():
        return 1 + 1

    @dbconnection.unit_of_work
    def uow_2():
        return uow_1()

    with pytest.raises(dbconnection.NestedUnitOfWorkError):
        uow_2()


def test_get_current_database_revision(db_session):
    assert dbconnection.get_current_database_revision() is not None
