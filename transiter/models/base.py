from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base


class _BaseModel:
    """
    Basic model that all Transiter models inherit from.

    This class defines an equals method for use in testing, and representation
    functions for outputting dictionary representations of entities in the service
    layer.
    """

    # The equals method is designed for testing purposes only.
    def __eq__(self, other):
        for column in inspect(type(self)).columns.keys():
            if getattr(self, column) != getattr(other, column):
                # print(
                #    'Values for attribute "{}" don\'t match: "{}" != "{}"'.format(
                #        column, str(getattr(self, column)), str(getattr(other, column))
                #    )
                # )
                return False
        return True

    # The __repr__ method is designed for testing purposes only.
    def __repr__(self):
        attributes = []
        for column in inspect(type(self)).columns.keys():
            attributes.append("{}={}".format(column, getattr(self, column)))
        return "{}({})".format(type(self).__name__, ", ".join(attributes))

    # This is a hack to get around a problem in SQL Alchemy where the hash is evaluated
    # It should not be relied on and will be replaced at some point by an exception!
    def __hash__(self):
        return id(self)


Base = declarative_base(cls=_BaseModel)


class ToDictMixin:

    __dict_columns__ = None
    __large_dict_columns__ = None

    def to_dict(self) -> dict:
        return self._to_dict(self.__dict_columns__)

    def to_large_dict(self) -> dict:
        return self._to_dict(self.__large_dict_columns__)

    def _to_dict(self, columns) -> dict:
        if columns is None:
            raise NotImplementedError
        return {column.key: getattr(self, column.key, None) for column in columns}
