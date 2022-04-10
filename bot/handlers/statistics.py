from aiogram import types

from dispatcher import (
	dp, bot
)

from config import MESSAGES

from utils.db import (
	get_statistics_db, get_user_db
)


async def process_statistics_control(msg: types.Message):
	user = await get_user_db(msg.from_user.username)
	statistics = await get_statistics_db(user.id)
	text = MESSAGES["statistics"].format(
		total_notes = f"{statistics.total_notes}",
		completed_notes = f"{statistics.completed_notes}",
		unfinished_notes = f"{statistics.unfinished_notes}",
	)

	await bot.send_message(msg.from_user.id, text)


def reqister_handler_statistics():
	dp.register_message_handler(process_statistics_control, commands = ["statistics"])
