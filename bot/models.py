from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from config import NAME_DB


engine = create_engine(f"sqlite:///{NAME_DB}.db")
Base = declarative_base()


class User(Base):
	"""docstring for User"""

	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	first_name = Column(String(255), nullable = False)
	username = Column(String(255), nullable = False)

	def __repr__(self):
		return f"{self.first_name}: {self.username}"
