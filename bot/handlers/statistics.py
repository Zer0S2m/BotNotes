from aiogram import types

from sqlalchemy.future import select

from models import Statistics
from models import User

from dispatcher import (
	dp, bot, Session
)

from config import MESSAGES


async def process_statistics_control(msg: types.Message):
	async with Session.begin() as session:
		user_id = await session.execute(select(User).filter_by(
			username = msg.from_user.username
		))
		user_id = user_id.scalars().first().id
		statistics = await session.execute(select(Statistics).filter_by(
			user_id = user_id
		))
		statistics = statistics.scalars().first()

		await session.close()

	text = MESSAGES["statistics"].format(
		total_notes = f"{statistics.total_notes}",
		completed_notes = f"{statistics.completed_notes}",
		unfinished_notes = f"{statistics.unfinished_notes}",
	)

	await bot.send_message(msg.from_user.id, text)


def reqister_handler_statistics():
	dp.register_message_handler(process_statistics_control, commands = ["statistics"])
