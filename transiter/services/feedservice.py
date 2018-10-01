from ..data.dbaccessobjects import FeedDao, FeedUpdateDao
from ..data import dbconnection
import importlib
import requests
import hashlib


feed_dao = FeedDao()
feed_update_dao = FeedUpdateDao()


@dbconnection.unit_of_work
def list_all_in_system(system_id):

    response = []

    for feed in feed_dao.list_all_in_system(system_id):
        feed_response = {
            'feed_id': feed.feed_id
            }
        response.append(feed_response)
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(system_id, feed_id):

    feed = feed_dao.get_in_system_by_id(system_id, feed_id)
    response = {
        'feed_id': feed.feed_id,
        'url': feed.url
        }
    return response


@dbconnection.unit_of_work
def create_feed_update(system_id, feed_id):

    feed = feed_dao.get_in_system_by_id(system_id, feed_id)

    feed_update = feed_update_dao.create()
    feed_update.feed = feed
    feed_update.status = 'SCHEDULED'

    # TODO make this asynchronous
    execute_feed_update(feed_update)
    return {'done': 'true'}


@dbconnection.unit_of_work
def list_updates_in_feed(system_id, feed_id):

    feed = feed_dao.get_in_system_by_id(system_id, feed_id)
    session = feed_update_dao.get_session()
    query = session.query(feed_update_dao._DbObj).filter(
        feed_update_dao._DbObj.feed_pri_key==feed.id
    ).order_by(feed_update_dao._DbObj.last_action_time.desc())
    response = []
    for feed_update in query:
        response.append(
            {
                'id': feed_update.id,
                'status': feed_update.status,
                'last_action_time': feed_update.last_action_time
            }
        )
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
    with open('./transiter/l2.gtfs', 'rb') as f:
        content = f.read()
    #request = requests.get(feed.url)
    #content = request.content
    #m = hashlib.md5()
    #m.update(content.encode('utf-8'))
    #print(m.hexdigest())
    try:
        update_function(feed, feed.system, content)
    except Exception:
        feed_update.status = 'FAILURE_COULD_NOT_PARSE'
    feed_update.status = 'SUCCESS_UPDATED'
