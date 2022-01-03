from aiogram import types
from aiogram.dispatcher import FSMContext

from config import MESSAGES

from models import User
from models import Statistics

from dispatcher import dp
from dispatcher import bot
from dispatcher import session


def create_table_statistics(username):
	if not session.query(Statistics).filter(
			Statistics.user_id == session.query(User).filter(User.username == username).first().id
		).first():

		user_id = session.query(User).filter(User.username == username).first().id

		new_statistics = Statistics(user_id = user_id)
		session.add(new_statistics)
		session.commit()


async def process_start_command(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	await state.finish()

	if not session.query(User).filter(User.username == msg.from_user.username).first():
		new_user = User(first_name = msg.from_user.first_name, username = msg.from_user.username)

		session.add(new_user)
		session.commit()

	create_table_statistics(username = msg.from_user.username)

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
