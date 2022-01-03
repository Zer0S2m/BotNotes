import os

from models import Base
from models import engine

from config import NAME_DB


if __name__ == '__main__':
	path = os.path.join(os.path.abspath(os.path.dirname(__file__)), f"{NAME_DB}.db")
	os.remove(path)

	Base.metadata.create_all(engine)
