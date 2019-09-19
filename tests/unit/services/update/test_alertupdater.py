import unittest
from unittest import mock

from transiter import models
from transiter.services.update import alertupdater
from ... import testutil


class TestAlertUpdater(testutil.TestCase(alertupdater), unittest.TestCase):
    SYSTEM_ID = "1"
    ALERT_1_ID = "2"
    ALERT_2_ID = "3"
    ALERT_3_ID = "4"
    ROUTE_1_ID = "5"
    ROUTE_2_ID = "6"
    ALERT_2_PK = 7

    def setUp(self):
        self.systemdam = self.mockImportedModule(alertupdater.systemdam)
        self.database = self.mockImportedModule(alertupdater.dbconnection)

    def test_sync_alerts(self):
        """[Alert updater] Sync alerts"""

        session = mock.MagicMock()
        self.database.get_session.return_value = session
        merged = []

        def merge(alert):
            merged.append(alert)
            return alert

        session.merge = merge

        system = models.System()
        route_1 = models.Route()
        route_1.id = self.ROUTE_1_ID
        route_2 = models.Route()
        route_2.id = self.ROUTE_2_ID
        system.routes = [route_1, route_2]

        expired_alert = models.Alert()
        expired_alert.id = self.ALERT_1_ID
        stale_alert = models.Alert()
        stale_alert.id = self.ALERT_2_ID
        stale_alert.route_ids = [self.ROUTE_1_ID]
        stale_alert.pk = self.ALERT_2_PK
        self.systemdam.list_all_alerts_in_system.return_value = [
            expired_alert,
            stale_alert,
        ]

        updated_alert = models.Alert()
        updated_alert.id = self.ALERT_2_ID
        updated_alert.route_ids = [self.ROUTE_1_ID, self.ROUTE_2_ID]
        new_alert = models.Alert()
        new_alert.id = self.ALERT_3_ID
        new_alert.route_ids = [self.ROUTE_2_ID]

        alertupdater.sync_alerts(system, [updated_alert, new_alert])

        self.assertEqual(updated_alert.pk, self.ALERT_2_PK)
        self.assertEqual(updated_alert.routes, [route_1, route_2])
        self.assertEqual(new_alert.routes, [route_2])

        session.delete.assert_called_once_with(expired_alert)
        self.assertEqual([updated_alert, new_alert], merged)
