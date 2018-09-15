from . import dbconnection
from . import schema

class InvalidIdError(Exception):
    pass

def list():
    session = dbconnection.get_session()

    for feed in session.query(schema.Feed):
        yield feed

def get(feed_id):
    session = dbconnection.get_session()
    try:
        return session.query(schema.Feed).filter(schema.Feed.feed_id==feed_id).one()
    except dbconnection.NoResultFound:
        raise InvalidIdError
