"""
The fast operations module contains methods for fast interactions with the database.
The cost is that these operations sacrifice the nice ORM behavior; for example, there
is no notion of cascading.
"""
import time

from transiter.data import dbconnection


class FastInserter:
    """
    Class for inserting entries into the database quickly.

    After initializing the class, entities are added via the add method which accepts
    a dictionary of the entity's data. Periodically, depending on the batch size,
    insert statements are issued to the database. To fully insert all elements it is
    necessary to manually call flush at the end.
    """

    def __init__(self, DbModel, batch_size=50000):
        """
        Initialize a new fast inserter.

        :param DbModel: the database model whose type will be inserted
        :param batch_size: the batch size. After this number of entities have been
            added, the entities will be inserted into the database. Batching the
            inserts is an optimization designed for some databases like Postgres
        """
        self._DbModel = DbModel
        self._batch_size = batch_size
        self._session = dbconnection.get_session()
        self._queue = []
        self._total_db_time = 0

    def add(self, data):
        """
        Add a new entity to be inserted.

        :param data: a dictionary of data for the entity; the keys are the entities
            attributes and the values are the desired values.
        """
        if len(self._queue) >= self._batch_size:
            self.flush()
        self._queue.append(data)

    def flush(self):
        """
        Insert the pending entities that have been added.
        """
        start_time = time.time()
        self._session.execute(self._DbModel.__table__.insert(), self._queue)
        self._total_db_time += time.time() - start_time
        self._queue = []
