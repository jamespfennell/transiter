from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect


class _BasicModel:

    def __eq__(self, other):
        for column in inspect(type(self)).columns.keys():
            if column == 'id':
                continue
            if getattr(self, column) != getattr(other, column):
                print('Values for attribute "{}" don\'t match!'.format(
                    column))
                print(' Model one: "' + str(getattr(self, column)) + '"')
                print(' Model two: "' + str(getattr(other, column)) + '"')
                return False
        return True

    def short_repr(self):
        return self._repr('_short_repr_list', '_short_repr_dict')

    def long_repr(self):
        return self._repr('_long_repr_list', '_long_repr_dict')

    def _repr(self, list_name, dict_name):
        if not hasattr(self, list_name) and not hasattr(self, dict_name):
            raise NotImplementedError
        repr_list = getattr(self, list_name, [])
        repr_dict = getattr(self, dict_name, {})
        full_repr_dict = {
            **repr_dict,
            **{key: key for key in repr_list},
        }
        return {
            key: getattr(self, value, None) for (key, value) in full_repr_dict.items()
        }


Base = declarative_base(cls=_BasicModel)


def model_eq(model_one, model_two):
    for column in inspect(type(model_one)).columns.keys():
        if column == 'id':
            continue
        if getattr(model_one, column) != getattr(model_two, column):
            print(column)
            print('-' + str(getattr(model_one, column)) + '-')
            print('-' + str(getattr(model_two, column)) + '-')
            return False
    return True


