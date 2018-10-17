from datetime import date, datetime
import json
import time

import flask

from transiter.utils import linksutil
from transiter.database import models

"""
class ContainerTypeError(Exception):
    pass

class ValueTypeError(Exception):
    pass
"""


def convert_for_http(data):
    return json.dumps(data, indent=4, separators=(',', ': '), default=json_serial)


def convert_for_cli(data):
    return json.dumps(data, indent=4, separators=(',', ': '))


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return (obj.timestamp() - time.time())/60#.isoformat()

    if isinstance(obj, linksutil.Link):
        return obj.url()

    raise TypeError ("Type %s not serializable" % type(obj))





def route_to_url(route):
    return flask.url_for(
        'route_endpoints.get_in_system_by_id',
        system_id=route.system_id,
        route_id=route.route_id, _external=True)

def stop_to_url(stop):
    return flask.url_for(
        'stop_endpoints.get_in_system_by_id',
        system_id=stop.system_id,
        stop_id=stop.stop_id, _external=True)

entity_type_to_href_generator = {
    models.Route: route_to_url,
    models.Stop: stop_to_url,
}

def entity_href_to_url(entity_href):

    entity = entity_href.entity
    if type(entity) in entity_type_to_href_generator:
        return entity_type_to_href_generator[type(entity)](entity)
    return 'Not implemented'

"""

_tab_string = "    "

def _type_to_str(value):
    t = type(value)
    if t is int:
        return str(value)
    if t is str:
        return '"{}"'.format(value)
    if t is bool:
        if value:
            return 'true'
        else:
            return 'false'
    if value is None:
        return 'null'
    if t is datetime.datetime:
        # Check if naive
        if value.tzinfo is not None and value.tzinfo.utcoffset(value) is not None:
            return int(value.timestamp())
        utc_dt = pytz.utc.localize(value)
        return int(utc_dt.timestamp())
    raise ValueTypeError('Unknown type "{}" for use as value.'.format(t))


def jsonify(root, indent=''):

    pre_json = []
    if type(root) is dict:

        pre_json.append(indent + '{ ')
        for key, value in root.items():
            t = type(value)
            try:
                pre_json.append(indent + _tab_string + '"{}" : {},'.format(key, _type_to_str(value)))
            except ValueTypeError:
                sub_json = jsonify(value, indent+_tab_string)
                pre_json.append(indent + _tab_string + '"{}" : {}'.format(key, sub_json.strip()))
        pre_json[-1] = pre_json[-1][:-1]
        pre_json.append(indent + '},')
    else:
        pre_json.append(indent + '[ ')
        try:
            for value in root:
                try:
                    pre_json.append(indent + _tab_string + '{},'.format(_type_to_str(value)))
                except ValueTypeError:
                    sub_json = jsonify(value, indent + _tab_string)
                    pre_json.append(sub_json)
        except:
            raise ContainerTypeError('Expected dict or iterable; got {}.'.format(type(root)))
        pre_json[-1] = pre_json[-1][:-1]
        pre_json.append(indent + '],')

    if indent == '':
        pre_json[-1] = pre_json[-1][:-1]

    return '\n'.join(pre_json)


"""