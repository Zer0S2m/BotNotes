from aiogram import types

from models import Statistics
from models import User

from dispatcher import bot
from dispatcher import session
from dispatcher import dp

from config import MESSAGES


async def process_statistics_control(msg: types.Message):
	user_id = session.query(User).filter(User.username == msg.from_user.username).first().id

	statistics = session.query(Statistics).filter_by(user_id = user_id).first()

	text = MESSAGES["statistics"].format(
		total_notes = f"{statistics.total_notes}",
		completed_notes = f"{statistics.completed_notes}",
		unfinished_notes = f"{statistics.unfinished_notes}",
	)

	await bot.send_message(msg.from_user.id, text)


def reqister_handler_statistics():
	dp.register_message_handler(process_statistics_control, commands = ["statistics"])
