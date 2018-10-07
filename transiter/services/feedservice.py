from ..database.accessobjects import FeedDao, FeedUpdateDao
from ..database import connection
import importlib
import time
import requests
import hashlib


feed_dao = FeedDao()
feed_update_dao = FeedUpdateDao()


@connection.unit_of_work
def list_all_in_system(system_id):

    response = []

    for feed in feed_dao.list_all_in_system(system_id):
        feed_response = {
            'feed_id': feed.feed_id,
            'href': 'NI',
            'last_update_time': 'NI',
            'health': {
                'status': 'NI'
            }
        }
        response.append(feed_response)
    return response


@connection.unit_of_work
def get_in_system_by_id(system_id, feed_id):

    feed = feed_dao.get_in_system_by_id(system_id, feed_id)
    response = {
        'feed_id': feed.feed_id,
        'last_update_time': 'NI',
        'health': {
            'status': 'NI',
            'score': 'NI',
            "update_types": [
                {
                    "status": "NI",
                    "failure_message": 'NI',
                    "fraction": 'NI'
                },
            ]
        }
        }
    return response


@connection.unit_of_work
def create_feed_update(system_id, feed_id):

    feed = feed_dao.get_in_system_by_id(system_id, feed_id)
    #print(feed.feed_id)
    feed_update = feed_update_dao.create()
    feed_update.feed = feed
    feed_update.status = 'SCHEDULED'

    # TODO make this asynchronous
    execute_feed_update(feed_update)
    #print(time.time())
    return {
        'href': 'NI'
    }


@connection.unit_of_work
def list_updates_in_feed(system_id, feed_id):

    feed = feed_dao.get_in_system_by_id(system_id, feed_id)
    session = feed_update_dao.get_session()
    query = session.query(feed_update_dao._DbObj).filter(
        feed_update_dao._DbObj.feed_pri_key==feed.id
    ).order_by(feed_update_dao._DbObj.last_action_time.desc())
    response = []
    for feed_update in query:
        response.append(feed_update.short_repr())
    return response


def execute_feed_update(feed_update):

    feed_update.status = 'IN_PROGRESS'
    #return {'created': 'tre'}

    importlib.invalidate_caches()
    feed = feed_update.feed
    # TODO Need to more flexible with these - maybe alpha numberic
    # Or maybe a separate system_dir_name
    # TODO These checks should also exist when installing
    if not feed.system.system_id.isalnum():
        raise IllegalSystemName
    if not feed.parser_module.isalpha():
        raise IllegalModuleName
    if not feed.parser_function.isalpha():
        raise IllegalFunctionName
    module_path = '...systems.{}.{}'.format(
        feed.system.system_id,
        feed.parser_module
        )
    module = importlib.import_module(module_path, __name__)
    update_function = getattr(module, feed.parser_function)


    if feed.feed_id == 'ServiceStatus':
        filename = 'ServiceStatusSubway.xml'
    else:
        filename = 'l2.gtfs'

    #with open('./transiter/{}'.format(filename), 'rb') as f:
    #    content = f.read()
    #print(feed.url)
    request = requests.get(feed.url)
    content = request.content

    print(time.time())
    m = hashlib.md5()
    m.update(content)
    feed_update.raw_data_hash = m.hexdigest()
    print(time.time())

    last_successful_update = feed_dao.get_last_successful_update(feed.id)
    print(time.time())
    if last_successful_update is not None and \
            last_successful_update.raw_data_hash == feed_update.raw_data_hash:
        feed_update.status = 'SUCCESS_NOT_NEEDED'
        return
    print(time.time())

    try:
        update_function(feed, feed.system, content)
        feed_update.status = 'SUCCESS_UPDATED'
    except Exception:
        feed_update.status = 'FAILURE_COULD_NOT_PARSE'
        raise
