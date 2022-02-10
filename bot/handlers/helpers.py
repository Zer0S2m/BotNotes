import re
import os
import datetime as DT

import sqlalchemy

from aiogram import types

from sqlalchemy.future import select

from models import (
	User, Note, Category,
	Statistics, File
)

from config import (
	FILE_EXTENSION, STATIC_FILES
)

from dispatcher import Session, bot

from config import DATE


async def add_db_new_note(data: dict):
	async with Session.begin() as session:
		new_note = Note(
			text = data["text"],
			user_id = data["user_id"]
		)

		if "title" in data:
			new_note.title = data["title"]

		if "category" in data:
			new_note.category_id = data["category"]

		if "file" in data:
			new_note.file_id = data["file"].id

		if ("number_day" in data) and ("number_month" in data) and ("number_year" in data):
			complete_date = set_complete_date_note({
				"number_year": data["number_year"],
				"number_month": data["number_month"],
				"number_day": data["number_day"]
			})
			new_note.complete_date = complete_date

		session.add(new_note)

		statistics = await session.execute(select(Statistics).filter_by(
			user_id = data["user_id"]
		))
		statistics = statistics.scalars().first()
		statistics.total_notes += 1

		await session.commit()


async def add_db_new_file(data: dict):
	async with Session.begin() as session:
		new_file = File(
			user_id = data["user_id"],
			file_path = data["file_path"],
			file_path_id = data["file_path_id"],
			file_extension = data["file_extension"]
		)

		session.add(new_file)


async def create_text_note(note: Note) -> dict:
	async with Session.begin() as session:
		date = await session.execute(select(Note).filter_by(
			id = note.id
		))
		date = date.scalars().first().pub_date

		pub_date = get_pub_date_note(date = date)

	text = f"<b>Описание</b> - {note.text}"

	if str(note.title)[0] != "0" and len(note.title) > 0:
		text = f"<b>Заголовок</b> - {note.title}\n{text}"

	if note.category_id:
		async with Session.begin() as session:
			category = await session.execute(select(Category).filter_by(
				id = note.category_id,
				user_id = note.user_id
			))
			category = category.scalars().first()
		text += f"\n\n<b>Категория</b> - {category.title.title()}"

	if str(note.complete_date)[0] != "0" and len(note.complete_date) > 0:
		complete_date_split = list(map(int, note.complete_date.split("-")))
		complete_date = get_pub_date_note(date = DT.datetime(*complete_date_split))
		complete_date = re.sub(r"\s\d{0,2}:\d{0,2}", "", complete_date)

		text += f"\n\n<b>Дата завершения</b> - {complete_date}"

	text += f"\n\n{pub_date}"
	file_path_id = None
	file_extension = None

	if note.file_id:
		async with Session.begin() as session:
			file = await session.execute(select(File).filter_by(
				id = note.file_id,
				user_id = note.user_id
			))
			file = file.scalars().first()

		file_path_id = file.file_path_id
		file_extension = file.file_extension

	return {
		"text": text,
		"file_path_id": file_path_id,
		"file_extension": file_extension
	}


def get_pub_date_note(date: DT.datetime) -> str:
	return f'{date.strftime("%d.%m.%Y")} {date.strftime("%H:%M")}'


def set_title_category(title: str) -> str:
	return title.strip().lower()


def change_dict_date(data: dict):
	""":param data - key: 'month'"""

	if data["month"] == 0:
		DATE["month"] = 12
		DATE["year"] = DATE["year"] - 1
	elif data["month"] == 13:
		DATE["month"] = 1
		DATE["year"] = DATE["year"] + 1
	else:
		DATE["month"] = data["month"]

def cleans_dict_date():
	DATE["day"] = DT.datetime.now().day
	DATE["month"] = DT.datetime.now().month
	DATE["year"] = DT.datetime.now().year


def parse_date(data: str) -> dict:
	number_day = re.search(r"day:(\d{0,2})", data)
	number_month = re.search(r"month:(\d{0,2})", data)
	number_year = re.search(r"year:(\d{0,4})", data)

	return {
		"number_day": number_day,
		"number_month": number_month,
		"number_year": number_year
	}


async def delete_note(
	username: str,
	data: str,
	action: str
	) -> bool:
	async with Session.begin() as session:
		user_id = await session.execute(select(User).filter_by(
			username = username
		))
		user_id = user_id.scalars().first().id
		note_id = re.search(r"\d{1,10}", data).group(0)

		note_deleted = await session.execute(select(Note).filter_by(
			user_id = user_id, id = note_id
		))
		note_deleted = note_deleted.scalars().first()

		try:
			if note_deleted.file_id:
				file = await session.execute(select(File).filter_by(
					id = note_deleted.file_id,
					user_id = delete_note.user_id
				))
				file = file.scalars().first()

				delete_file_deleted_note(file.file_path)

			await session.delete(note_deleted)

		except sqlalchemy.orm.exc.UnmappedInstanceError:
			return True

		statistics = await session.execute(select(Statistics).filter_by(
			user_id = user_id
		))
		statistics = statistics.scalars().first()

		if action == "delete":
			statistics.unfinished_notes += 1
		elif action == "complete":
			statistics.completed_notes += 1

		await session.commit()

		return False


def delete_file_deleted_note(path_file: str):
	os.remove(path_file)


async def set_category_for_update_note(data: dict) -> dict:
	if "category_id" in data:
		async with Session.begin() as session:
			user_id = await session.execute(select(User).filter_by(
				username = data["username"]
			))
			user_id = user_id.scalars().first().id

			category_id = await session.execute(select(Category).filter_by(
				user_id = user_id,
				title = data["category_id"].lower()
			))
			category_id = category_id.scalars().first().id

			data["category_id"] = category_id

	return data


async def update_note(data: dict):
	if len(data.items()) <= 2:
		return False

	data = await set_category_for_update_note(data)
	data = set_complete_date_update_note(data)

	async with Session.begin() as session:
		user_id = await session.execute(select(User).filter_by(
			username = data["username"]
		))
		user_id = user_id.scalars().first().id

		update_note = await session.execute(select(Note).filter_by(
			user_id = user_id, id = data["note_id"]
		))
		update_note = update_note.scalars().first()

		if update_note.file_id and "file" in data:
			await update_file_db(update_note, data)

		if "file" in data:
			print(True)
			await add_db_new_file(data= {
				"file_path": data["file"]["directory"],
				"file_path_id": data["file"]["file_id"],
				"file_extension": data["file"]["file_extension"],
				"user_id": user_id
			})

			await bot.download_file(
				data["file"]["file_path"],
				data["file"]["directory"]
			)

			new_file = await session.execute(select(File).filter_by(
				user_id = user_id,
				file_path_id = data["file"]["file_id"]
			))
			new_file = new_file.scalars().first()
			print(new_file)

			del data["file"]

			data["file_id"] = new_file.id

		update_params_note_db(update_note, data)

async def update_file_db(note: Note, data: dict):
	async with Session.begin() as session:
		file = await session.execute(select(File).filter_by(
			id = note.file_id,
			user_id = note.user_id
		))
		file = file.scalars().first()

		delete_file_deleted_note(file.file_path)

	await bot.download_file(
		data["file"]["file_path"],
		data["file"]["directory"]
	)

	data["file"]["file_path"] = data["file"]["directory"]
	data["file"]["file_path_id"] = data["file"]["file_id"]

	async with Session.begin() as session:
		current_file = await session.execute(select(File).filter_by(
			id = note.file_id,
			user_id = note.user_id
		))
		current_file = current_file.scalars().first()

	for key, value in data["file"].items():
		setattr(current_file, key, value)

def update_params_note_db(note: Note, data: dict):
	for key, value in data.items():
		if key != "note_id" and key != "username" and key != "file":
			setattr(note, key, value)


def set_complete_date_update_note(data: dict) -> dict:
	if "complete_date" in data:
		data["complete_date"] = set_complete_date_note({
			"number_year": data["complete_date"]["number_year"],
			"number_month": data["complete_date"]["number_month"],
			"number_day": data["complete_date"]["number_day"]
		})

	return data


def set_complete_date_note(data: dict) -> DT.date:
	return DT.date(data["number_year"], data["number_month"], data["number_day"])


async def get_categories(username: str) -> list:
	categories = []

	async with Session.begin() as session:
		user_id = await session.execute(select(User).filter_by(
			username = username
		))
		user_id = user_id.scalars().first().id
		categories_select = await session.execute(select(Category).filter_by(
			user_id = user_id
		))
		categories = categories_select.scalars().all()

	return categories


def set_choice_date(parse_date: dict) -> DT.datetime:
	return DT.datetime(
		int(parse_date["number_year"].group(1)),
		int(parse_date["number_month"].group(1)),
		int(parse_date["number_day"].group(1)),
		23, 59, 59
	)


def set_choice_date_for_text(choice_date: DT.datetime) -> str:
	choice_date = get_pub_date_note(date = choice_date)
	choice_date = re.sub(r"\s\d{0,2}:\d{0,2}", "", choice_date)

	return choice_date


async def set_settings_file_for_note(msg: types.Message) -> dict:
	if msg.document:
		file_id = msg.document.file_id
		file_extension = FILE_EXTENSION["doc"]

	elif msg.photo:
		file_id = msg.photo[len(msg.photo) - 1].file_id
		file_extension = FILE_EXTENSION["photo"]

	elif msg.audio:
		file_id = msg.audio.file_id
		file_extension = FILE_EXTENSION["audio"]

	file = await bot.get_file(file_id)
	file_path = file.file_path
	file_name = file_path.split("/")[-1]
	directory = f'{STATIC_FILES}/{file_path.split("/")[0]}/{file_name}'

	return {
		"file_id": file_id,
		"file_extension": file_extension,
		"directory": directory,
		"file_path": file_path
	}
