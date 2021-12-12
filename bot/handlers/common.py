from aiogram import types
from aiogram.dispatcher import FSMContext

from config import MESSAGES

from models import User

from dispatcher import dp
from dispatcher import bot
from dispatcher import session


async def process_start_command(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	await state.finish()

	if not session.query(User).filter(User.username == msg.from_user.username).first():
		new_user = User(first_name = msg.from_user.first_name, username = msg.from_user.username)

		session.add(new_user)
		session.commit()

	await bot.send_message(msg.from_user.id, MESSAGES["start"].format(name = msg.from_user.first_name))


async def process_help_command(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)
	await state.finish()

	await bot.send_message(msg.from_user.id, MESSAGES["help"])


async def process_info_command(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)
	await state.finish()

	await bot.send_message(msg.from_user.id, MESSAGES["info"])


async def cmd_cancel(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer("Команда отменена!", reply_markup = types.ReplyKeyboardRemove())
