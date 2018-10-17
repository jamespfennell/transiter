import datetime
import re
from xml.etree import ElementTree

from transiter.database import models
from transiter.database import syncutil
from transiter.database.daos import route_dao, route_status_dao


def update(feed, system, content):

    parser = ServiceStatusXmlParser(content)
    data = parser.parse()
    db_messages = route_status_dao.get_all_in_system(system.system_id)
    route_id_to_route = {route.route_id: route
                         for route in route_dao.list_all_in_system(system.system_id)}
    for status in data:
        status['routes'] = [route_id_to_route[route_id]
                            for route_id in status['route_ids']]
        del status['route_ids']
    syncutil.sync(models.RouteStatus, db_messages, data, ['status_id'])
    return True


class ServiceStatusXmlParser:

    NAMESPACE = '{http://www.siri.org.uk/siri}'

    def __init__(self, raw_xml):
        self._raw_xml = raw_xml

    def parse(self):
        data = []
        root = ElementTree.fromstring(self._raw_xml)
        situations = self._find_descendent_element(root, 'Situations')
        for situation in situations:
            xml_tag_to_dict_key = {
                'status_id': 'SituationNumber',
                'status_type': 'ReasonName',
                'status_priority': 'MessagePriority',
                'message_title': 'ReasonName',
                'message_content': 'Description',
                'creation_time': 'CreationTime'
            }
            situation_data = {
                dict_key: self._get_content_in_child_element(situation, xml_tag)
                for dict_key, xml_tag in xml_tag_to_dict_key.items()
            }
            situation_data['status_priority'] = int(situation_data['status_priority'])

            publication_window = self._find_child_element(
                situation, 'PublicationWindow')
            situation_data['start_time'] = self._get_content_in_child_element(
                publication_window, 'StartTime')
            situation_data['end_time'] = self._get_content_in_child_element(
                publication_window, 'EndTime')

            for key in ('creation_time', 'end_time', 'start_time'):
                situation_data[key] = self._time_string_to_datetime(situation_data[key])

            affected_routes = []
            for route_string in self._get_content_in_descendent_elements(
                    situation, 'LineRef'):
                index = route_string.rfind('_')
                affected_routes.append(route_string[index+1:])
            situation_data['route_ids'] = affected_routes

            data.append(situation_data)
        return data

    @classmethod
    def _get_content_in_child_element(cls, element, tag):
        child_element = cls._find_child_element(element, tag)
        if child_element is None:
            return None
        return child_element.text.strip()

    @classmethod
    def _find_child_element(cls, element, tag):
        return element.find(cls.NAMESPACE + tag)

    @classmethod
    def _find_descendent_element(cls, element, tag):
        for descendent in element.iter(cls.NAMESPACE + tag):
            return descendent

    @classmethod
    def _get_content_in_descendent_elements(cls, element, tag):
        for descendent in element.iter(cls.NAMESPACE + tag):
            yield descendent.text.strip()

    @staticmethod
    def _time_string_to_datetime(time_string):
        if time_string is None:
            return None
        # First remove any microseconds
        time_string = re.sub('\.[0-9]+', '', time_string)
        return datetime.datetime.fromisoformat(time_string)

