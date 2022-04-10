import datetime as DT
from typing import List

from sqlalchemy import and_
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from dispatcher import Session
from dispatcher import bot

from models import (
	Note, Category, File,
	Statistics, User
)

from utils.common import (
	set_complete_date_note, delete_file_local_storage, set_complete_date_update_note,
	update_params_note_db
)


async def get_user_db(username: str) -> User:
	async with Session.begin() as session:
		user = await session.execute(
			select(User)
			.filter_by(username = username)
			.options(selectinload(User.notes))
		)
		user = user.scalars().first()

	return user


async def create_user_db(
	username: str,
	first_name: str
) -> User:
	async with Session.begin() as session:
		new_user = User(
			first_name = first_name,
			username = username
		)
		session.add(new_user)

	return new_user


async def get_category_db(
	user_id: int,
	title: str
) -> Category:
	async with Session.begin() as session:
		category = await session.execute(
			select(Category).filter_by(title = title, user_id = user_id)
		)
		category = category.scalars().first()

	return category


async def create_category_db(
	user_id: int,
	title: str
):
	async with Session.begin() as session:
		new_category = Category(
			title = title,
			user_id = user_id
		)
		session.add(new_category)


async def delete_category_db(
	user_id: int,
	title: str
):
	async with Session.begin() as session:
		category = await session.execute(
			select(Category).filter_by(title = title, user_id = user_id)
		)
		category = category.scalars().first()
		await session.delete(category)


async def get_categories_db(user_id: int) -> List[Category]:
	async with Session.begin() as session:
		categories = await session.execute(
			select(Category).filter_by(user_id = user_id)
		)
		categories = categories.scalars().all()

	return categories


async def create_file_db(data: dict) -> File:
	async with Session.begin() as session:
		new_file = File(
			user_id = data["user_id"],
			file_path = data["file_path"],
			file_path_id = data["file_path_id"],
			file_extension = data["file_extension"]
		)

		session.add(new_file)

	return new_file


async def edit_file_db(
	note: Note,
	data: dict
):
	async with Session.begin() as session:
		current_file = await session.execute(
			select(File).filter_by(id = note.file_id,user_id = note.user_id)
		)
		current_file = current_file.scalars().first()

		delete_file_local_storage(current_file.file_path)

	await bot.download_file(
		data["file"]["file_path"],
		data["file"]["directory"]
	)

	data["file"]["file_path"] = data["file"]["directory"]
	data["file"]["file_path_id"] = data["file"]["file_id"]

	for key, value in data["file"].items():
		setattr(current_file, key, value)


async def get_notes_db(user_id: int) -> List[Note]:
	async with Session.begin() as session:
		notes = await session.execute(
			select(Note)
			.filter_by(user_id = user_id)
			.options(selectinload(Note.category), selectinload(Note.file))
		)
		notes = notes.scalars().all()

	return notes


async def get_notes_at_category(
	user_id: int,
	category_id: int
) -> List[Note]:
	async with Session.begin() as session:
		notes = await session.execute(
			select(Note)
			.filter_by(category_id = category_id, user_id = user_id)
			.options(selectinload(Note.category), selectinload(Note.file))
		)
		notes = notes.scalars().all()

	return notes


async def get_notes_on_date_db(
	user_id: int,
	dates: List[DT.datetime]
) -> List[Note]:
	async with Session.begin() as session:
		notes = await session.execute(
			select(Note)
			.filter(
				Note.user_id == user_id,
				and_(Note.pub_date >= dates[0], Note.pub_date <= dates[1])
			)
			.options(selectinload(Note.category), selectinload(Note.file))
		)
		notes = notes.scalars().all()

	return notes


async def create_note_db(data: dict):
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


async def delete_note_db(
	user_id: int,
	note_id: str,
	action: str,
) -> bool:
	async with Session.begin() as session:
		note_deleted = await session.execute(
			select(Note)
			.filter_by(user_id = user_id, id = note_id)
			.options(selectinload(Note.file))
		)
		note_deleted = note_deleted.scalars().first()

		if not note_deleted:
			return True

		if note_deleted.file:
			delete_file_local_storage(note_deleted.file.file_path)

		await session.delete(note_deleted)

		statistics = await session.execute(
			select(Statistics).filter_by(user_id = user_id)
		)
		statistics = statistics.scalars().first()

		if action == "delete":
			statistics.unfinished_notes += 1
		elif action == "complete":
			statistics.completed_notes += 1

		await session.commit()

	return False


async def set_category_for_update_note(
	data: dict,
	user_id: int
) -> dict:
	if "category_id" in data:
		category = await get_category_db(user_id, data["category_id"].lower())
		data["category_id"] = category.id

	return data


async def edit_note_db(data: dict):
	if len(data.items()) <= 2:
		return False

	user = await get_user_db(data["username"])
	data = await set_category_for_update_note(data, user.id)
	data = set_complete_date_update_note(data)

	async with Session.begin() as session:
		update_note = await session.execute(select(Note).filter_by(
			user_id = user.id, id = data["note_id"]
		))
		update_note = update_note.scalars().first()

		if update_note.file_id and "file" in data:
			await edit_file_db(update_note, data)

		if "file" in data:
			new_file = await create_file_db({
				"file_path": data["file"]["directory"],
				"file_path_id": data["file"]["file_id"],
				"file_extension": data["file"]["file_extension"],
				"user_id": user.id
			})

			await bot.download_file(
				data["file"]["file_path"],
				data["file"]["directory"]
			)

			del data["file"]

			data["file_id"] = new_file.id

		update_params_note_db(update_note, data)



async def get_statistics_db(user_id: int) -> Statistics:
	async with Session.begin() as session:
		statistics = await session.execute(
			select(Statistics).filter_by(user_id = user_id)
		)
		statistics = statistics.scalars().first()

	return statistics


async def create_statistics_db(user_id: int):
	async with Session.begin() as session:
		statistics = await session.execute(select(Statistics).filter_by(
			user_id = user_id
		))

		if not statistics.scalars().first():
			new_statistics = Statistics(user_id = user_id)
			session.add(new_statistics)
