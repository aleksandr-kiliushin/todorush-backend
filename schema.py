from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True)
	telegram_id = Column(BigInteger, nullable=True, unique=True)

class Task(Base):
	__tablename__ = 'task'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	title = Column(String(255), nullable=False)
	description = Column(String(1000), nullable=True)
	due_date = Column(DateTime, nullable=True)

	user = relationship('User', back_populates='tasks')

# Create a back-reference in the User class
User.tasks = relationship('Task', back_populates='user')
