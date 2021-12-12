from aiogram import types

from config import MESSAGES

from models import User

from dispatcher import bot
from dispatcher import session


async def process_start_command(msg: types.Message):
	if not session.query(User).filter(User.username == msg.from_user.username).first():
		new_user = User(first_name = msg.from_user.first_name, username = msg.from_user.username)

		session.add(new_user)
		session.commit()

	await bot.send_message(msg.from_user.id, MESSAGES["start"])


async def process_help_command(msg: types.Message):
	await bot.send_message(msg.from_user.id, MESSAGES["help"])


async def process_info_command(msg: types.Message):
	await bot.send_message(msg.from_user.id, MESSAGES["info"])
