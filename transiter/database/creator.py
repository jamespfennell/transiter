from transiter import models
from . import connection
import sqlalchemy



def create_database(db_name='realtimerail', user='james'):
    engine = sqlalchemy.create_engine("postgres://{}@/postgres".format(user))
    conn = engine.connect()
    try:
        conn.execute("commit")
        conn.execute("DROP DATABASE {}".format(db_name))
    except sqlalchemy.exc.ProgrammingError:
        pass
    conn.execute("commit")
    conn.execute("CREATE DATABASE {}".format(db_name))
    conn.close()


def create_tables():
    models.Base.metadata.create_all(connection.engine)

