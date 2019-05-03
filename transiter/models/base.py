from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base


class _BasicModel:
    """
    Basic model that all Transiter models inherit from.

    This class defines an equals method for use in testing, and representation
    functions for outputting dictionary representations of entities in the service
    layer.
    """

    def __eq__(self, other):
        for column in inspect(type(self)).columns.keys():
            # if column == "pk":
            #    continue
            if getattr(self, column) != getattr(other, column):
                print('Values for attribute "{}" don\'t match!'.format(column))
                print(' Model one: "' + str(getattr(self, column)) + '"')
                print(' Model two: "' + str(getattr(other, column)) + '"')
                return False
        return True

    def __repr__(self):
        return str(self.pk)

    # Hack to get around a bug/design problem in SQL Alchemy
    # Should not be relied on!
    def __hash__(self):
        return id(self)

    def short_repr(self):
        return self._repr("_short_repr_list", "_short_repr_dict")

    def long_repr(self):
        return self._repr("_long_repr_list", "_long_repr_dict")

    def _repr(self, list_name, dict_name):
        if not hasattr(self, list_name) and not hasattr(self, dict_name):
            raise NotImplementedError
        repr_list = getattr(self, list_name, [])
        repr_dict = getattr(self, dict_name, {})
        full_repr_dict = {**repr_dict, **{key: key for key in repr_list}}
        return {
            key: getattr(self, value, None) for (key, value) in full_repr_dict.items()
        }


Base = declarative_base(cls=_BasicModel)
