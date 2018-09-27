import xml.etree.ElementTree as ET
import json
from ...data import dbconnection
from ...data import dbsync
from ...data import dbschema
def jsonify(data):
    return json.dumps(data, indent=4, separators=(',', ': '))


def update(feed, service, content):
    feed_messages = parse(content)

    session = dbconnection.get_session()
    routes = {route.route_id: route for route in session.query(dbschema.Route)}

    for message in feed_messages.values():
        message['routes'] = [routes[route_id] for route_id in message['route_ids']]
        print(message['routes'])
        del message['route_ids']
    db_messages = set(session.query(dbschema.StatusMessage))
    # What to do about routes? Could manually add them
    # to the JSON - yes
    dbsync.sync(dbschema.StatusMessage, db_messages, feed_messages.values(), ['message_id'])

    return True


def parse(content):

    month_index_to_name = ['Jan', 'Feb', 'Mar',
        'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
        'Oct', 'Nov', 'Dec']
    try:
        root = ET.fromstring(content)
    except Exception as e:
        print('Invalid XML file.')
        print(e)
        return False



    namespace = '{http://www.siri.org.uk/siri}'
    feed_time = root[0][0].text


    for situations in root.iter(namespace + 'Situations'):
        new_messages = {}
        for situation in situations:

            message_time = situation.find(namespace + 'CreationTime').text
            year = int(message_time[0:4])
            month = int(message_time[5:7])
            day = int(message_time[8:10])
            hour = int(message_time[11:13])
            minute = int(message_time[14:16])
            message_data = {}

            message_data['message_id'] = situation.find(namespace + 'SituationNumber').text.strip()
            if situation.find(namespace + 'Planned').text.strip() != 'true':
                message_data['time_posted'] = "Posted {:s} {:d} {:d} at {:02d}:{:02d}.".format(month_index_to_name[month-1], day, year, hour, minute)
            else:
                message_data['time_posted'] = "Posted {:s} {:d} {:d}.".format(month_index_to_name[month-1], day, year, hour, minute)

            message_data['message'] = situation.find(namespace + 'Description').text
            message_data['message_type'] = situation.find(namespace + 'ReasonName').text

            affected_routes = set()
            for route in situation.find(namespace + 'Affects').iter(namespace + 'LineRef'):
                route_id = route.text.strip()[-1]
                if route_id == 'I':
                    route_id = 'SI'
                affected_routes.add(route_id)
            """
            for route in affected_routes:
                if route == 'I':
                    message_data['route_id'] = 'SI'
                else:
                    message_data['route_id'] = route
            """
            message_data['route_ids'] = list(affected_routes)
            new_messages[message_data['message_id']] = message_data
    return new_messages
