from .data import dbconnection
from .data import schema
import sqlalchemy

from .services import systemservice


def create_database():
    engine = sqlalchemy.create_engine("postgres://james@/postgres")
    conn = engine.connect()
    try:
        conn.execute("commit")
        conn.execute("DROP DATABASE realtimerail")
    except sqlalchemy.exc.ProgrammingError:
        pass
    conn.execute("commit")
    conn.execute("CREATE DATABASE realtimerail")
    conn.close()

def create_tables():
    schema.Base.metadata.create_all(dbconnection.engine)

create_database()
create_tables()
systemservice.install('nycsubway')
