from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect


Base = declarative_base()


def model_eq(model_one, model_two):
    for column in inspect(type(model_one)).columns.keys():
        if column == 'id':
            continue
        if getattr(model_one, column) != getattr(model_two, column):
            print('fail')
            print('-' + str(getattr(model_one, column)) + '-')
            print('-' + str(getattr(model_two, column)) + '-')
            return False
    return True


