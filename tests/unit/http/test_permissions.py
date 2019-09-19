import unittest

from transiter import exceptions
from transiter.http import permissions
from .. import testutil


class TestPermissions(testutil.TestCase(permissions), unittest.TestCase):
    def setUp(self):
        flask = self.mockImportedModule(permissions.flask)
        self.headers = flask.request.headers

    def test_invalid_request_permissions_level(self):
        """[Permissions validator] Invalid request permissions level"""
        self.headers.get.return_value = "GarbageStatus"

        self.assertRaises(
            exceptions.InvalidPermissionsLevelInRequest,
            permissions.ensure,
            permissions.PermissionsLevel.ALL,
        )

    def test_no_permission(self):
        """[Permissions validator] Does not have permission"""
        self.headers.get.return_value = permissions.PermissionsLevel.ADMIN_READ.name

        self.assertRaises(
            exceptions.AccessDenied,
            permissions.ensure,
            permissions.PermissionsLevel.ALL,
        )

    def test_has_permission(self):
        """[Permissions validator] Has permission"""
        self.headers.get.return_value = permissions.PermissionsLevel.ALL.name

        permissions.ensure(permissions.PermissionsLevel.ADMIN_READ)
