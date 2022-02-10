from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from sqlalchemy.future import select

import emoji

from config import MESSAGES

from models import User
from models import Statistics

from dispatcher import (
	dp, bot, Session
)


async def create_table_statistics(username: str):
	async with Session.begin() as session:
		user_id = await session.execute(select(User).filter_by(
			username = username
		))
		user_id = user_id.scalars().first().id
		statistics = await session.execute(select(Statistics).filter_by(
			user_id = user_id
		))

		if not statistics.scalars().first():
			new_statistics = Statistics(user_id = user_id)
			session.add(new_statistics)


async def process_start_command(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	await state.finish()

	async with Session.begin() as session:
		user = await session.execute(select(User).filter_by(
			username = msg.from_user.username
		))

		if not user.scalars().first():
			new_user = User(
				first_name = msg.from_user.first_name,
				username = msg.from_user.username
			)

			session.add(new_user)

	await create_table_statistics(username = msg.from_user.username)

	await bot.send_message(msg.from_user.id, MESSAGES["start"].format(name = msg.from_user.first_name))


async def process_help_command(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	await state.finish()

	await bot.send_message(msg.from_user.id, MESSAGES["help"])


async def process_info_command(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)
	await state.finish()

	await bot.send_message(msg.from_user.id, MESSAGES["info"])


async def cmd_cancel(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer(emoji.emojize("Команда отменена :cross_mark:"), reply_markup = types.ReplyKeyboardRemove())


def reqister_handler_common():
	dp.register_message_handler(process_start_command, commands = ['start'], state = "*")
	dp.register_message_handler(process_help_command, commands = ["help"])
	dp.register_message_handler(process_info_command, commands = ["info"], state = "*")
	dp.register_message_handler(cmd_cancel, commands = ["cancel"], state = "*")
	dp.register_message_handler(cmd_cancel, Text(equals = "отмена", ignore_case = True), state = "*")
