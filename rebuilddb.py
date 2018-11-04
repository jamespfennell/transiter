from transiter.database import creator
from transiter.services import systemservice


if __name__ == '__main__':
    creator.create_database()
    creator.create_tables()
    systemservice.install('nycsubway')
