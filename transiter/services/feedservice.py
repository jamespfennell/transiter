from ..data import feeddam
from ..data import dbconnection
import importlib
import requests
import hashlib

@dbconnection.unit_of_work
def list():

    response = []

    for feed in feeddam.list():
        feed_response = {
            'feed_id': feed.feed_id
            }
        response.append(feed_response)
    return response


@dbconnection.unit_of_work
def get(feed_id):

    feed = feeddam.get(feed_id)
    response = {
        'feed_id': feed.feed_id,
        'url': feed.url
        }
    return response

@dbconnection.unit_of_work
def update(feed_id):
    importlib.invalidate_caches()
    feed = feeddam.get(feed_id)
    # Need to more flexible with these - maybe alpha numberic
    # Or maybe a separate system_dir_name
    if not feed.system.system_id.isalnum():
        raise IllegalSystemeName
    if not feed.parser_module.isalpha():
        raise IllegalModuleName
    if not feed.parser_function.isalpha():
        raise IllegalFunctionName
    module_path = '...systems.{}.{}'.format(
        feed.system.system_id,
        feed.parser_module
        )
    module = importlib.import_module(module_path, __name__)
    function = getattr(module, feed.parser_function)
    with open('./transiter/l2.gtfs', 'rb') as f:
        content = f.read()
    #request = requests.get(feed.url)
    #content = request.content
    #m = hashlib.md5()
    #m.update(content.encode('utf-8'))
    #print(m.hexdigest())
    function(feed, feed.system, content)
