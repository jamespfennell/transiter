import importlib
#from .protobuf import gtfs_realtime_pb2
#from .protobuf import nyc_subway_pb2
from google.transit import gtfs_realtime_pb2
import json

def jsonify(data):
    return json.dumps(data, indent=4, separators=(',', ': '))


class GtfsExtension():

    def __init__(self, pb_module, base_module):
        self._pb_module = pb_module
        self._base_module = base_module

    def activate(self):
        importlib.import_module(self._pb_module, self._base_module)

def gtfs_to_json(content, extension=None):
    if extension is not None:
        extension.activate()
    gtfs_feed = gtfs_realtime_pb2.FeedMessage()
    gtfs_feed.ParseFromString(content)
    #print(jsonify(_parse_protobuf_message(gtfs_feed)))
    return(_parse_protobuf_message(gtfs_feed))

def _identity(value):
    return value

def _parse_protobuf_message(message):
    """
    Input is of type a google.protobuf.message.Message
    Returns a dictionary of {key: value}
    """
    d = {}
    for (descriptor, value) in message.ListFields():
        # if descriptor.type = 11, this is a message field
        # Recursively parse it with the function
        # Otherwise just return the value
        if descriptor.type == 11:
            parsing_function = _parse_protobuf_message
        else:
            parsing_function = _identity

        # If this is a repeated field
        if descriptor.label == 3:
            parsed_value = [parsing_function(v) for v in value]
        else:
            parsed_value = parsing_function(value)

        d[descriptor.name] = parsed_value

    return d
