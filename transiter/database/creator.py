from . import models
from . import connection
import sqlalchemy



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
    models.Base.metadata.create_all(connection.engine)

