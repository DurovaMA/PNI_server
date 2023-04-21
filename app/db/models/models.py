from sqlalchemy import Column, Integer, ForeignKey, VARCHAR, UniqueConstraint, SMALLINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(VARCHAR(50), nullable=True)
    password = Column(VARCHAR(300), nullable=True)
    email = Column(VARCHAR(40))

    UniqueConstraint(username, name='username')
    UniqueConstraint(email, name='email')


class Parametr(Base):
    __tablename__ = 'parametr'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    title = Column(VARCHAR, nullable=True)
    symbol = Column(VARCHAR, nullable=False)
    units = Column(VARCHAR, nullable=True)
    param_type = Column(Integer, nullable=False)

    UniqueConstraint(id, name='id')


class Environment(Base):
    __tablename__ = 'environment'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    type_of_environment = Column(VARCHAR, nullable=True)

    UniqueConstraint(id, name='parametrid')

