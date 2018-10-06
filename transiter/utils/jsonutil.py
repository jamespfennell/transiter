from datetime import date, datetime
import json

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
        return obj.timestamp() #.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

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