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

    _short_repr_list = []
    _short_repr_dict = {}
    _long_repr_list = []
    _long_repr_dict = {}

    def short_repr(self):
        """
        Get the short representation of the entity.

        :return: dictionary
        """
        return self._repr(self._short_repr_list, self._short_repr_dict)

    def long_repr(self):
        """
        Get the long representation of the entity.

        :return: dictionary
        """
        return self._repr(self._long_repr_list, self._long_repr_dict)

    def _repr(self, repr_list, repr_dict):
        """
        Get a representation of the entity.

        :param repr_list: a list of SQL Alchemy columns types
        :param repr_dict: map of string to SQL Alchemy column types
        :return: map where the keys are the keys in the dict combined with the column
             names in the list, and the values are values of associated columns.
        :raises NotImplementedError: if the list and dict have length 0
        """
        full_repr_dict = {
            **{key: column.key for key, column in repr_dict.items()},
            **{column.key: column.key for column in repr_list},
        }
        if len(full_repr_dict) == 0:
            raise NotImplementedError
        return {
            key: getattr(self, value, None) for (key, value) in full_repr_dict.items()
        }


Base = declarative_base(cls=_BaseModel)
