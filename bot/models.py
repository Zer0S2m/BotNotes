from datetime import datetime

from sqlalchemy import (
	Column, Integer, String,
	DateTime, ForeignKey, Text
)
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from config import (
	NAME_DB, LIMIT_TITLE, LIMIT_TEXT,
	LIMIT_CATEGORY
)


engine = create_engine(f"sqlite:///{NAME_DB}.db")
Base = declarative_base()


class User(Base):
	"""docstring for User"""

	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	first_name = Column(String(255), nullable = False)
	username = Column(String(255), nullable = False)
	notes = relationship("Note", backref = "user_notes", cascade = "all, delete")
	categories = relationship("Category", backref = "user_categories", cascade = "all, delete")
	statistics = relationship("Statistics", backref = "user_statistics", cascade = "all, delete")

	def __repr__(self):
		return f"<{self.first_name}> - <username: {self.username}>"


class Note(Base):
	"""docstring for Note"""

	__tablename__ = "note"

	id = Column(Integer, primary_key = True)
	title = Column(String(LIMIT_TITLE), default = False, info = {"limit": LIMIT_TITLE})
	text = Column(Text(LIMIT_TEXT), nullable = False, info = {"limit": LIMIT_TEXT})
	pub_date = Column(DateTime, default = datetime.now(), nullable = False)
	user_id = Column(Integer, ForeignKey('user.id'))
	category = relationship("Category", backref = "note_category", uselist = False)
	category_id = Column(Integer, ForeignKey('category.id', ondelete = "CASCADE"), default = False)


	def __repr__(self):
		return f"<id-user: {self.user_id}> - <id-note: {self.id}>"


class Category(Base):
	"""docstring for Category"""

	__tablename__ = "category"

	id = Column(Integer, primary_key = True)
	title = Column(String(LIMIT_CATEGORY), default = False, info = {"limit": LIMIT_CATEGORY})
	user_id = Column(Integer, ForeignKey('user.id'))


	def __repr__(self):
		return f"<id-user: {self.user_id}> - <title-category: {self.title}>"


class Statistics(Base):
	"""docstring for Statistics"""

	__tablename__ = "statistics"

	id = Column(Integer, primary_key = True)
	user_id = Column(Integer, ForeignKey('user.id'))
	total_notes = Column(Integer, default = 0)
	completed_notes = Column(Integer, default = 0)
	unfinished_notes = Column(Integer, default = 0)


	def __repr__(self):
		return f"<id-user: {self.user_id}> - <id: {self.id}>"
