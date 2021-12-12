import re

from aiogram import types
from aiogram.dispatcher import FSMContext

from config import (
	INFO_TEXT, LIMIT_CATEGORY
)

from models import (
	User, Note, Category
)

from state import FSMFormCategory
from state import StatesCategory

from dispatcher import bot
from dispatcher import dp
from dispatcher import session

import keyboards


async def process_create_category(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)

	await FSMFormCategory.title.set()

	await bot.send_message(callback_query.from_user.id, "Запишите название категории:")


async def process_create_category_state(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()
	user_id = session.query(User).filter(User.username == msg.from_user.username).first().id

	if len(title) > LIMIT_CATEGORY:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	elif len(re.findall(r"^[\d\W]", title)) > 0:
		await msg.reply(
			f"Название категория не может начинаться с <b>символов</b> или с <b>цифры</b>!\nПерезапишите название!\n{INFO_TEXT}"
		)

	elif session.query(Category).filter_by(
		title = title, user_id = user_id
	).first():
		await msg.reply("Категория с таким названием уже существует!\nПерезапишите название:")

	else:
		new_category = Category(
			title = msg.text.strip(),
			user_id = user_id
		)

		session.add(new_category)
		session.commit()

		await state.finish()
		await msg.reply("Категория создана!")


async def process_view_category(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)

	user_id = session.query(User).filter(User.username == callback_query.from_user.username).first().id
	categories = session.query(Category).filter_by(user_id = user_id).all()

	if not categories:
		await bot.send_message(callback_query.from_user.id, "Категории отсуствуют!")

	else:
		text = "Категории:\n"

		for category_in in range(0, len(categories)):
			notes_at_category = len(session.query(Note).filter_by(
				category_id = categories[category_in].id, user_id = user_id
			).all())
			text += f"\n{category_in + 1}) {categories[category_in].title} ({notes_at_category})"

		await bot.send_message(callback_query.from_user.id, text)


async def process_delete_category(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)

	user_id = session.query(User).filter(User.username == callback_query.from_user.username).first().id
	categories = session.query(Category).filter(Category.user_id == user_id).all()

	if not categories:
		await bot.send_message(callback_query.from_user.id, "Категории для удаления отсуствуют!")

	else:
		state = dp.current_state(user = callback_query.from_user.id)
		await state.set_state(StatesCategory.all()[StatesCategory.all().index("state_delete_category")])

		await bot.send_message(
			callback_query.from_user.id,
			f"Укажите категорию:",
			reply_markup = keyboards.create_btns_for_choice_categories(categories)
		)


async def process_delete_category_state(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()
	user_id = session.query(User).filter(User.username == msg.from_user.username).first().id

	if title == "-":
		await bot.send_message(
			msg.from_user.id,
			f"Команда отменена!",
			reply_markup = types.ReplyKeyboardRemove()
		)

		await state.reset_state()

	else:
		category_deleted = session.query(Category).filter_by(
			title = title, user_id = user_id
		).first()

		if not category_deleted:
			await bot.send_message(
				msg.from_user.id,
				"Данной категории не существует!\nПерезапишите название:"
			)

		else:
			session.delete(category_deleted)
			session.commit()

			await bot.send_message(
				msg.from_user.id,
				f"Категория удалена!",
				reply_markup = types.ReplyKeyboardRemove()
			)

			await state.reset_state()


async def process_category_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление категориями",
		reply_markup = keyboards.control_categories
	)
