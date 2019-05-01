from transiter.data.dams import systemdam
from . import dbtestutil, testdata


class TestSystemDAM(dbtestutil.TestCase):
    def test__system_dao__count_stops_in_system(self):
        """[System DAM] Count number of stops"""
        count = systemdam.count_stops_in_system(testdata.SYSTEM_ONE_ID)

        self.assertEqual(7, count)

    def test__system_dao__count_routes_in_system(self):
        """[System DAM] Count number of stops"""
        count = systemdam.count_routes_in_system(testdata.SYSTEM_ONE_ID)

        self.assertEqual(3, count)

    def test__system_dao__count_feeds_in_system(self):
        """[System DAM] Count number of stops"""
        count = systemdam.count_feeds_in_system(testdata.SYSTEM_ONE_ID)

        self.assertEqual(2, count)

    def test__base_entity_dao__list_all(self):
        """[System DAM] List all systems"""
        self.assertListEqual(
            [testdata.system_one, testdata.system_two], systemdam.list_all()
        )

    def test__base_entity_dao__get_by_id(self):
        """[System DAM] Get by ID"""
        db_system = systemdam.get_by_id(testdata.SYSTEM_ONE_ID)

        self.assertEqual(testdata.system_one, db_system)

    def test__base_entity_dao__get_by_id__no_result(self):
        """[System DAM] Get by ID - no result"""
        db_system = systemdam.get_by_id(testdata.SYSTEM_THREE_ID)

        self.assertEqual(None, db_system)

    def test__base_entity_dao__create(self):
        """[System DAM] Create new system"""
        self.assertEqual(None, systemdam.get_by_id(testdata.SYSTEM_THREE_ID))

        db_system = systemdam.create()
        db_system.id = testdata.SYSTEM_THREE_ID
        db_system.name = testdata.SYSTEM_THREE_NAME
        db_system.package = testdata.SYSTEM_THREE_PACKAGE
        self.session.flush()

        self.assertEqual(db_system, systemdam.get_by_id(testdata.SYSTEM_THREE_ID))

    def test__base_entity_dao__delete(self):
        """[System DAM] Delete a system"""
        self.assertEqual(
            testdata.system_two, systemdam.get_by_id(testdata.SYSTEM_TWO_ID)
        )

        response = systemdam.delete_by_id(testdata.SYSTEM_TWO_ID)
        self.session.flush()

        self.assertTrue(response)
        self.assertEqual(None, systemdam.get_by_id(testdata.SYSTEM_TWO_ID))

    def test__base_entity_dao__delete__none_to_delete(self):
        """[System DAM] Delete a system - none to delete"""
        response = systemdam.delete_by_id(testdata.SYSTEM_THREE_ID)

        self.assertFalse(response)

    def test_list_all_alerts_in_system(self):
        """[System DAM] Get all alerts in system"""
        self.assertEqual(
            {testdata.alert_1, testdata.alert_2, testdata.alert_3, testdata.alert_4},
            set(systemdam.list_all_alerts_in_system(testdata.SYSTEM_ONE_ID)),
        )
