import unittest
import unittest.mock as mock
from transiter.http import permissionsvalidator


class TestValidatePermissions(unittest.TestCase):

    def setUp(self):
        self.flask_patch = mock.patch(
            'transiter.http.permissionsvalidator.request')
        self.request = self.flask_patch.start()
        self.addCleanup(self.flask_patch.stop)
        self.headers = self.request.headers

    def test_bad_request(self):
        """[Permissions validator] Bad request"""
        self.headers.get.return_value = 'GarbageStatus'

        self.assertRaises(
            permissionsvalidator.UnknownPermissionsLevelInRequest,
            permissionsvalidator.validate_permissions,
            'All')

    def test_bad_method_call(self):
        """[Permissions validator] Bad method call"""
        self.headers.get.return_value = 'All'

        self.assertRaises(
            permissionsvalidator.UnknownPermissionsLevelInMethod,
            permissionsvalidator.validate_permissions,
            'GarbageStatus')

    def test_no_permission(self):
        """[Permissions validator] No permission"""
        self.headers.get.return_value = 'AdminRead'

        self.assertRaises(
            permissionsvalidator.AccessDenied,
            permissionsvalidator.validate_permissions,
            'All')

    def test_has_permission(self):
        """[Permissions validator] Bad request"""
        self.headers.get.return_value = 'All'

        permissionsvalidator.validate_permissions('AdminRead')
