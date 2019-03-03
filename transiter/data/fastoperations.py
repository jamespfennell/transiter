from transiter.data import database
import time


class FastInserter:

    def __init__(self, DbModel, batch_size=50000):
        self._DbModel = DbModel
        self._batch_size = batch_size
        self._session = database.get_session()
        self._queue = []
        self._total_db_time = 0

    def add(self, data):
        self._queue.append(data)
        if len(self._queue) > self._batch_size:
            self.flush()

    def flush(self):
        start_time = time.time()
        self._session.execute(
            self._DbModel.__table__.insert(),
            self._queue
        )
        self._total_db_time += time.time() - start_time
        self._queue = []
