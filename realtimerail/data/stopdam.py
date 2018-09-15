from . import dbconnection
from . import schema

class InvalidIdError(Exception):
    pass

def list():
    session = dbconnection.get_session()

    for stop in session.query(schema.Stop).order_by(schema.Stop.name):
        yield stop

def get(stop_id):
    session = dbconnection.get_session()
    try:
        return session.query(schema.Stop).filter(schema.Stop.stop_id==stop_id).one()
    except database.NoResultFound:
        raise InvalidIdError
