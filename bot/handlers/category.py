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
from state import FSMFormNote

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

	if len(title) > LIMIT_CATEGORY:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	elif len(re.findall(r"^[\d\W]", title)) > 0:
		await msg.reply(
			f"Название категория не может начинаться с <b>символов</b> или с <b>цифры</b>!\nПерезапишите название!\n{INFO_TEXT}"
		)

	elif session.query(Category).filter(Category.title == title).first():
		await msg.reply("Категория с таким названием уже существует!\nПерезапишите название:")

	else:
		new_category = Category(
			title = msg.text.strip(),
			user_id = session.query(User).filter(User.username == msg.from_user.username).first().id
		)

		session.add(new_category)
		session.commit()

		await state.finish()
		await msg.reply("Категория создана!")


async def process_view_category(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)

	categories = session.query(Category).filter(User.username == callback_query.from_user.username).all()

	if not categories:
		await bot.send_message(callback_query.from_user.id, "Категории отсуствуют!")

	else:
		text = "Категории:\n"

		for category_in in range(0, len(categories)):
			notes_at_category = len(session.query(Note).filter(Note.category_id == categories[category_in].id).all())
			text += f"\n{category_in + 1}) {categories[category_in].title} ({notes_at_category})"

		await bot.send_message(callback_query.from_user.id, text)


async def process_category_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление категориями",
		reply_markup = keyboards.control_categories
	)
