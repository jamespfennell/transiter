import unittest
from unittest import mock
from transiter.general import linksutil


class TestLinks(unittest.TestCase):

    URL = 'Url'

    @mock.patch('transiter.general.linksutil.flask')
    def test_entity_links(self, flask):
        flask.url_for.return_value = self.URL
        model = mock.MagicMock()
        link_classes = [
            linksutil.FeedEntityLink,
            linksutil.FeedsInSystemIndexLink,
            linksutil.StopEntityLink,
            linksutil.StopsInSystemIndexLink,
            linksutil.SystemEntityLink,
            linksutil.RouteEntityLink,
            linksutil.RoutesInSystemIndexLink,
            linksutil.TripEntityLink
        ]
        for link_class in link_classes:
            link = link_class(model)

            actual = link.url()

            self.assertEqual(actual, self.URL)

            flask.url_for.assert_called_with(
                link.endpoint,
                _external=True,
                **link.kwargs)


    def test_broken_link(self):
        link = linksutil.Link()

        self.assertRaises(NotImplementedError, link.url)


