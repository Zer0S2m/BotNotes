from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

import emoji

from config import MESSAGES

from dispatcher import (
	dp, bot
)

from utils.db import (
	create_user_db, get_user_db, create_statistics_db
)


async def process_start_command(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	await state.finish()

	user = await get_user_db(msg.from_user.username)
	if not user:
		user = await create_user_db(msg.from_user.username, msg.from_user.first_name)

	await create_statistics_db(user.id)

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
