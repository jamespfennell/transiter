from . import dbconnection
from . import schema
from sqlalchemy.orm.exc import NoResultFound

def get(system_id):
    session = dbconnection.get_session()
    try:
        return session.query(schema.System).filter(schema.System.system_id==system_id).one()
    except NoResultFound:
        return None

def list_all():
    session = dbconnection.get_session()
    return [system for system in session.query(schema.System).order_by(schema.System.system_id)]

def create():
    session = dbconnection.get_session()
    system = schema.System()
    session.add(system)
    return system

def delete(system_id):
    session = dbconnection.get_session()
    system = get(system_id)
    if system is not None:
        session.delete(system)
