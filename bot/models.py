from datetime import datetime

from sqlalchemy import (
	Column, Integer, String,
	DateTime, ForeignKey, Text
)
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
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
	notes = relationship("Note", back_populates = "user")

	def __repr__(self):
		return f"{self.first_name}: <username: {self.username}>"


class Note(Base):
	"""docstring for Note"""

	__tablename__ = "note"

	id = Column(Integer, primary_key = True)
	title = Column(String(255))
	text = Column(Text(1000), nullable = False)
	pub_date = Column(DateTime, default = datetime.now(), nullable = False)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship("User", back_populates = "notes")


	def __repr__(self):
		return f"{self.title} - <id: {self.id}>"
