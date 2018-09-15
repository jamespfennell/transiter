from . import dbconnection
from . import schema

class InvalidIdError(Exception):
    pass

def list():
    session = dbconnection.get_session()

    for route in session.query(schema.Route).order_by(schema.Route.route_id):
        yield route

def get(route_id):
    session = dbconnection.get_session()
    try:
        return session.query(schema.Route).filter(schema.Route.route_id==route_id).one()
    except database.NoResultFound:
        raise InvalidIdError
