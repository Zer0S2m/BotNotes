import re

import emoji

from aiogram import types
from aiogram.dispatcher import FSMContext

from config import (
	INFO_TEXT, LIMIT_CATEGORY
)

from state import (
	FSMFormCategory, StatesCategory
)

from dispatcher import (
	dp, bot
)

from utils.db import (
	get_user_db, get_category_db, create_category_db,
	get_categories_db, delete_category_db, get_notes_at_category
)
from utils.common import (
	set_title_category
)

import keyboards


async def process_create_category(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)
	await FSMFormCategory.title.set()
	await bot.send_message(call.from_user.id, "Запишите название категории:")


async def process_create_category_state(msg: types.Message, state: FSMContext):
	title = set_title_category(title = msg.text)
	user = await get_user_db(msg.from_user.username)
	category = await get_category_db(user.id, title)

	if len(title) > LIMIT_CATEGORY:
		text_reply = f"Превышен лимит символов!\n{INFO_TEXT}"

	elif len(re.findall(r"^[\d\W]", title)) > 0:
		text_reply = \
			f"Название категория не может начинаться с <b>символов</b> или с <b>цифры</b>!\nПерезапишите название!\n{INFO_TEXT}"

	elif category:
		text_reply = "Категория с таким названием уже существует!\nПерезапишите название:"

	else:
		await create_category_db(user.id, title)
		await state.finish()
		text_reply = "Категория создана!"

	await msg.reply(text_reply)


async def process_view_category(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	user = await get_user_db(call.from_user.username)
	categories = await get_categories_db(user.id)

	if not categories:
		await bot.send_message(call.from_user.id, "Категории отсуствуют!")

	else:
		text = "Категории:\n"

		for category_in in range(0, len(categories)):
			notes_at_category = await get_notes_at_category(user.id, categories[category_in].id)
			count_notes_at_category = len(notes_at_category)

			text += f"\n{category_in + 1}) {categories[category_in].title.title()} ({count_notes_at_category})"

		await bot.send_message(call.from_user.id, text)


async def process_delete_category(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	user = await get_user_db(call.from_user.username)
	categories = await get_categories_db(user.id)

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
	state = dp.current_state(user = msg.from_user.id)
	title = set_title_category(msg.text)
	user = await get_user_db(msg.from_user.username)
	category = await get_category_db(user.id, title)

	if title == "-":
		reply_markup = types.ReplyKeyboardRemove()
		text_send_msg = emoji.emojize("Команда отменена :cross_mark:")
		await state.reset_state()
	elif not category:
		reply_markup = {}
		text_send_msg = "Данной категории не существует! Перезапишите название:"
	else:
		await delete_category_db(user.id, title)
		await state.reset_state()

		reply_markup = types.ReplyKeyboardRemove()
		text_send_msg = emoji.emojize("Категория удалена :cross_mark:")

	await bot.send_message(
		msg.from_user.id,
		text_send_msg,
		reply_markup = reply_markup
	)


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
