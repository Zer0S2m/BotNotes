import re

from aiogram import types
from aiogram.dispatcher import FSMContext

import emoji

from config import (
	INFO_TEXT, LIMIT_CATEGORY
)

from models import (
	User, Note, Category
)

from state import FSMFormCategory
from state import StatesCategory

from dispatcher import (
	dp, bot, Session
)

from handlers import helpers

import keyboards


async def process_create_category(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	await FSMFormCategory.title.set()

	await bot.send_message(call.from_user.id, "Запишите название категории:")


async def process_create_category_state(msg: types.Message, state: FSMContext):
	title = helpers.set_title_category(title = msg.text)

	with Session.begin() as session:
		user_id = session.query(User).filter(
			User.username == msg.from_user.username
		).first().id
		category = session.query(Category).filter_by(
			title = title, user_id = user_id
		).first()

	if len(title) > LIMIT_CATEGORY:
		text_reply = f"Превышен лимит символов!\n{INFO_TEXT}"

	elif len(re.findall(r"^[\d\W]", title)) > 0:
		text_reply = \
			f"Название категория не может начинаться с <b>символов</b> или с <b>цифры</b>!\nПерезапишите название!\n{INFO_TEXT}"

	elif category:
		text_reply = "Категория с таким названием уже существует!\nПерезапишите название:"

	else:
		with Session.begin() as session:
			new_category = Category(
				title = title,
				user_id = user_id
			)

			session.add(new_category)

		await state.finish()
		text_reply = "Категория создана!"

	await msg.reply(text_reply)


async def process_view_category(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	username = call.from_user.username
	categories = await helpers.get_categories(username = username)

	if not categories:
		await bot.send_message(call.from_user.id, "Категории отсуствуют!")

	else:
		text = "Категории:\n"

		for category_in in range(0, len(categories)):
			with Session.begin() as session:
				user_id = session.query(User).filter_by(
					username = username
				).first().id
				notes_at_category = len(session.query(Note).filter_by(
					category_id = categories[category_in].id, user_id = user_id
				).all())

			text += f"\n{category_in + 1}) {categories[category_in].title.title()} ({notes_at_category})"

		await bot.send_message(call.from_user.id, text)


async def process_delete_category(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	categories = await helpers.get_categories(username = call.from_user.username)

	if not categories:
		await bot.send_message(call.from_user.id, "Категории для удаления отсуствуют!")

	else:
		state = dp.current_state(user = call.from_user.id)
		await state.set_state(StatesCategory.all()[StatesCategory.all().index("state_delete_category")])

		await bot.send_message(
			call.from_user.id,
			f"Укажите категорию:",
			reply_markup = keyboards.create_btns_for_choice_categories(categories)
		)


async def process_delete_category_state(msg: types.Message):
	with Session.begin() as session:
		user_id = session.query(User).filter(User.username == msg.from_user.username).first().id

	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()

	category_deleted = False
	with Session.begin() as session:
		category_deleted = session.query(Category).filter_by(
			title = title, user_id = user_id
		).first()

		if not category_deleted:
			reply_markup = False
			text_send_msg = "Данной категории не существует!\nПерезапишите название:"

		else:
			session.delete(category_deleted)
			await state.reset_state()

			reply_markup = types.ReplyKeyboardRemove()
			text_send_msg = emoji.emojize("Категория удалена :cross_mark:")

		await bot.send_message(msg.from_user.id, text_send_msg, reply_markup = reply_markup)


async def process_category_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление категориями",
		reply_markup = keyboards.control_categories
	)


def	reqister_handler_category():
	dp.register_message_handler(process_category_control, commands = ["category"])
	dp.register_message_handler(process_create_category_state, state = FSMFormCategory.title)
	dp.register_message_handler(process_delete_category_state, state = StatesCategory.STATE_DELETE_CATEGORY)

	dp.register_callback_query_handler(process_create_category, lambda c: c.data == 'create_category')
	dp.register_callback_query_handler(process_delete_category, lambda c: c.data == 'delete_category')
	dp.register_callback_query_handler(process_view_category, lambda c: c.data == 'view_category')
