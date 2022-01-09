from models import Base
from models import engine


if __name__ == '__main__':
	Base.metadata.create_all(engine)
