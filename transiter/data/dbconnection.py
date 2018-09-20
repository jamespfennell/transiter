from decorator import decorator
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgres://james@/realtimerail")
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Fail hard if doesn't exist -> means not in a unit of work context
def get_session():
    return Session()

#Need to this to allow nesting of read sessions
# Fail hard if a nested write session is attempted
@decorator
def unit_of_work(func, *args, **kw):
    session = Session()
    try:
        result = func(*args, **kw)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        Session.remove()

    return result
