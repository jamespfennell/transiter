from .database import creator
from .services import systemservice


if __name__ == '__main__':
    creator.create_database()
    creator.create_tables()
    systemservice.install('nycsubway')
