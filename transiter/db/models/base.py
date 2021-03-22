from sqlalchemy import inspect
from sqlalchemy.orm import declarative_base


class _BaseModel:
    """
    Basic model that all Transiter models inherit from.

    This class defines an equals method for use in testing.
    """

    # The equals method is designed for testing purposes only.
    def __eq__(self, other):
        for column in inspect(type(self)).columns.keys():
            if getattr(self, column) != getattr(other, column, None):
                print(
                    'Values for attribute "{}" don\'t match: "{}" != "{}"'.format(
                        column,
                        str(getattr(self, column)),
                        str(getattr(other, column, "<not present>")),
                    )
                )
                return False
        return True

    # The __repr__ method is designed for testing purposes only.
    def __repr__(self):  # pragma: no cover
        attributes = []
        for column in inspect(type(self)).columns.keys():
            attributes.append("{}={}".format(column, getattr(self, column)))
        return "{}({})".format(type(self).__name__, ", ".join(attributes))

    # This is a hack to get around a problem in SQL Alchemy where the hash is evaluated
    # when setting models.Alert.routes = [...].
    def __hash__(self):
        return id(self)


Base = declarative_base(cls=_BaseModel)
