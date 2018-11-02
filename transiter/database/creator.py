from . import models
from . import connection
import sqlalchemy



def create_database(db_name='realtimerail'):
    engine = sqlalchemy.create_engine("postgres://postgres@/postgres")
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

