from sqlalchemy import Column, Integer, BigInteger, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True)
	telegram_id = Column(BigInteger, nullable=True, unique=True)
