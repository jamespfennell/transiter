import time
from unittest import mock

import pytest
from click.testing import CliRunner
from sqlalchemy import exc

from transiter import clt
from transiter.db import dbconnection
from transiter.executor import celeryapp
from transiter.http import flaskapp
from transiter.scheduler import client, server as scheduler


@pytest.fixture
def upgrade_database(monkeypatch):
    upgrade_database = mock.MagicMock()
    monkeypatch.setattr(dbconnection, "upgrade_database", upgrade_database)
    return upgrade_database


@pytest.fixture
def get_current_database_revision(monkeypatch):
    get_current_database_revision = mock.MagicMock()
    monkeypatch.setattr(
        dbconnection, "get_current_database_revision", get_current_database_revision
    )
    return get_current_database_revision


@pytest.fixture
def run_command():
    runner = CliRunner()

    def run(command):
        runner.invoke(clt.transiter_clt, command)

    return run


@pytest.mark.parametrize(
    "command,expected_args", [[["webservice"], [False]], [["-f", "webservice"], [True]]]
)
def test_launch_flask_app(run_command, monkeypatch, command, expected_args):
    launch = mock.MagicMock()
    monkeypatch.setattr(flaskapp, "launch", launch)

    run_command(["launch"] + command)

    launch.assert_called_once_with(*expected_args)


def test_launch_scheduler(run_command, monkeypatch):
    app = mock.MagicMock()
    monkeypatch.setattr(scheduler, "create_app", lambda: app)

    run_command(["launch", "scheduler"])

    app.run.assert_called_once()


@pytest.mark.parametrize(
    "command,expected_args",
    [[["executor"], ["warning"]], [["-l", "info", "executor"], ["info"]]],
)
def test_launch_executor(run_command, monkeypatch, command, expected_args):
    run_app = mock.MagicMock()
    monkeypatch.setattr(celeryapp, "run", run_app)

    run_command(["launch"] + command)

    run_app.assert_called_with(*expected_args)


@pytest.mark.parametrize(
    [
        "db_initialized",
        "revision_should_error",
        "upgrade_should_error",
        "num_expected_upgrade_calls",
    ],
    [
        [True, False, False, 0],
        [True, True, False, 0],
        [False, False, False, 1],
        [False, False, True, 2],
        [False, True, False, 1],
        [False, True, True, 2],
    ],
)
def test_init(
    run_command,
    monkeypatch,
    upgrade_database,
    get_current_database_revision,
    db_initialized,
    revision_should_error,
    upgrade_should_error,
    num_expected_upgrade_calls,
):
    # Just to make the test faster
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    def upgrade():
        nonlocal upgrade_should_error, db_initialized
        if upgrade_should_error:
            upgrade_should_error = False
            raise exc.SQLAlchemyError
        db_initialized = True

    def revision():
        nonlocal revision_should_error, db_initialized
        if revision_should_error:
            revision_should_error = False
            raise exc.SQLAlchemyError
        if db_initialized:
            return "dummy-alembic-hash"
        return None

    upgrade_database.side_effect = upgrade
    get_current_database_revision.side_effect = revision

    run_command(["db", "init"])

    upgrade_database.assert_has_calls(
        [mock.call() for __ in range(num_expected_upgrade_calls)]
    )


def test_upgrade(run_command, upgrade_database):
    run_command(["db", "upgrade"])

    upgrade_database.assert_called_once_with()


@pytest.mark.parametrize(
    "command,num_expected_calls", [[["reset", "--yes"], 1], [["reset"], 0]]
)
def test_reset(run_command, upgrade_database, monkeypatch, command, num_expected_calls):
    monkeypatch.setattr(dbconnection, "delete_all_tables", mock.MagicMock())
    monkeypatch.setattr(client, "refresh_tasks", mock.MagicMock())

    run_command(["db"] + command)

    upgrade_database.assert_has_calls([mock.call() for __ in range(num_expected_calls)])
