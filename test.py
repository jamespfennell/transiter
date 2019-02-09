from sqlalchemy import Column, Integer, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship


Base = declarative_base()


class Parent(Base):
    __tablename__ = 'parent'

    pk = Column(Integer, primary_key=True)

    children = relationship(
        'Child',
        cascade='delete, delete-orphan'
    )


class Child(Base):
    __tablename__ = 'child'

    pk = Column(Integer, primary_key=True)
    parent_pk = Column(Integer, ForeignKey('parent.pk'), nullable=False)

    parent = relationship(
        'Parent',
        back_populates='children',
        cascade='delete'
    )


engine = create_engine('postgresql://james@/realtimerail')
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
session = Session()

# To create the tables, before testing run
# Base.metadata.create_all(database.engine)

parent = Parent()
child_1 = Child()
child_1.parent = parent
child_2 = Child()
child_2.parent = parent

session.add(parent)
session.add(child_1)

session.commit()


