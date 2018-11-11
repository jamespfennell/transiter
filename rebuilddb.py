from transiter.database import creator
from transiter.services import systemservice
import os

if __name__ == '__main__':
    db_name = os.environ.get('TRANSITER_DB_NAME', 'realtimerail')
    creator.create_database(db_name)
    creator.create_tables()
    # systemservice.install('nycsubway')
