import importlib
import requests
import hashlib
from transiter.general import linksutil

from transiter.services.update import tripupdater, gtfsrealtimeutil
#client.refresh_jobs()


from transiter.data import database
from transiter.data.dams import feeddam

@database.unit_of_work
def list_all_in_system(system_id):

    response = []

    for feed in feeddam.list_all_in_system(system_id):
        feed_response = feed.short_repr()
        feed_response.update({
            'href': linksutil.FeedEntityLink(feed),
            'last_update': 'NI',
        })
        response.append(feed_response)
    return response


@database.unit_of_work
def get_in_system_by_id(system_id, feed_id):

    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    response = feed.short_repr()
    response.update({
        'last_update': 'NI',
        #'health': {
        #    'status': 'NI',
        #    'score': 'NI',
        #    "update_types": [
        #        {
        #            "status": "NI",
        #            "failure_message": 'NI',
        #            "fraction": 'NI'
        #        },
        #    ]
        #}
    })
    return response


@database.unit_of_work
def create_feed_update(system_id, feed_id):

    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    #print(feed.feed_id)
    feed_update = feeddam.create_update()
    feed_update.feed = feed
    feed_update.status = 'SCHEDULED'

    # TODO make this asynchronous
    _execute_feed_update(feed_update)

    #print(time.time())
    return {
        'href': 'NI'
    }


@database.unit_of_work
def list_updates_in_feed(system_id, feed_id):
    # TODO optimize this to only be one query? yes yes
    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    response = []
    for feed_update in feeddam.list_updates_in_feed(feed):
        response.append(feed_update.short_repr())
    return response


def _execute_feed_update(feed_update):
    feed_update.status = 'IN_PROGRESS'

    feed = feed_update.feed
    if feed.parser == 'custom':
        # TODO is this really necessary? Does it slow things down?
        importlib.invalidate_caches()
        # TODO Need to more flexible with these - maybe alpha numberic
        # TODO These checks should also exist when installing
        """
        if not feed.system.system_id.isalnum():
            raise IllegalSystemName
        if not feed.parser_module.isalpha():
            raise IllegalModuleName
        if not feed.parser_function.isalpha():
            raise IllegalFunctionName
        """
        module_path = '{}.{}'.format(
            feed.system.package,
            feed.custom_module
            )
        module = importlib.import_module(module_path)
        update_function = getattr(module, feed.custom_function)
    elif feed.parser == 'gtfsrealtime':
        update_function = _gtfs_realtime_parser
    else:
        raise Exception('Unknown feed parser')







    request = requests.get(feed.url)
    # TODO: raise for status here to catch HTTP errors
    content = request.content

    m = hashlib.md5()
    m.update(content)
    print(m.hexdigest())
    feed_update.raw_data_hash = m.hexdigest()

    last_successful_update = feeddam.get_last_successful_update(feed.pk)
    if last_successful_update is not None and \
            last_successful_update.raw_data_hash == feed_update.raw_data_hash:
        feed_update.status = 'SUCCESS_NOT_NEEDED'
        return

    try:
        update_function(feed, content)
        feed_update.status = 'SUCCESS_UPDATED'
    except Exception:
        print('Could not parse feed {}'.format(feed.id))
        feed_update.status = 'FAILURE_COULD_NOT_PARSE'


# TODO: move to GTFS realtime util? Or updatemanager.py?
def _gtfs_realtime_parser(feed, content):

    gtfs_data = gtfsrealtimeutil.read_gtfs_realtime(content)
    (__, __, trips) = gtfsrealtimeutil.transform_to_transiter_structure(
        gtfs_data, 'America/New_York')
    tripupdater.sync_trips(feed.system, None, trips)
