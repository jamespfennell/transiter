from transiter.data import database
from transiter.services import systemservice
import os

if __name__ == '__main__':
    db_name = os.environ.get('TRANSITER_DB_NAME', 'realtimerail')
    database.drop_database(db_name)
    database.create_database(db_name)
    database.create_tables()
    #systemservice.install('nycsubway')
