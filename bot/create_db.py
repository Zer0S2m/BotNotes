import asyncio

from models import Base
from models import engine


async def main():
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)


if __name__ == '__main__':
	asyncio.run(main())
