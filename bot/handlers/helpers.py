import re
import os
import datetime as DT

import sqlalchemy

from models import (
	User, Note, Category,
	Statistics, File
)

from dispatcher import Session

from config import DATE


def add_db_new_note(data: dict, username: str):
	with Session.begin() as session:
		user_id = session.query(User).filter(User.username == username).first().id
		new_note = Note(
			text = data["text"],
			user_id = user_id
		)

		if "title" in data:
			new_note.title = data["title"]

		if "category" in data:
			new_note.category_id = data["category"]

		if "file" in data:
			new_note.file_id = data["file"]

		if ("number_day" in data) and ("number_month" in data) and ("number_year" in data):
			complete_date = DT.date(data["number_year"], data["number_month"], data["number_day"])
			new_note.complete_date = complete_date

		session.add(new_note)

		statistics = session.query(Statistics).filter_by(user_id = user_id).first()
		statistics.total_notes += 1

		session.commit()


def add_db_new_file(data: dict, username: str):
	with Session.begin() as session:
		user_id = session.query(User).filter(User.username == username).first().id
		new_file = File(
			user_id = user_id,
			file_path = data["file_path"],
			file_path_id = data["file_path_id"],
			file_extension = data["file_extension"]
		)

		session.add(new_file)


def create_text_note(note: Note) -> dict:
	with Session.begin() as session:
		pub_date = get_pub_date_note(
			date = session.query(Note).filter_by(
				id = note.id
			).first().pub_date
		)

	text = f"<b>Описание</b> - {note.text}"

	if str(note.title)[0] != "0" and len(note.title) > 0:
		text = f"<b>Заголовок</b> - {note.title}\n{text}"

	if note.category:
		text += f"\n\n<b>Категория</b> - {note.category.title}"

	if str(note.complete_date)[0] != "0" and len(note.complete_date) > 0:
		complete_date_split = list(map(int, note.complete_date.split("-")))
		complete_date = get_pub_date_note(date = DT.datetime(*complete_date_split))
		complete_date = re.sub(r"\s\d{0,2}:\d{0,2}", "", complete_date)

		text += f"\n\n<b>Дата завершения</b> - {complete_date}"

	text += f"\n\n{pub_date}"
	file_path_id = None
	file_extension = None

	if note.file:
		file_path_id = note.file.file_path_id
		file_extension = note.file.file_extension

	return {
		"text": text,
		"file_path_id": file_path_id,
		"file_extension": file_extension
	}


def get_pub_date_note(date: DT.datetime) -> str:
	return f'{date.strftime("%d.%m.%Y")} {date.strftime("%H:%M")}'


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


def delete_note(
	username: str,
	data: str,
	action: str
) -> bool:
	with Session.begin() as session:
		user_id = session.query(User).filter(User.username == username).first().id
		note_id = re.search(r"\d{1,10}", data).group(0)

		note_deleted = session.query(Note).filter_by(
			user_id = user_id, id = note_id
		).first()

		try:
			if note_deleted.file:
				delete_file_deleted_note(note_deleted.file.file_path)

			session.delete(note_deleted)
		except sqlalchemy.orm.exc.UnmappedInstanceError:
			return True

		statistics = session.query(Statistics).filter_by(user_id = user_id).first()

		if action == "delete":
			statistics.unfinished_notes += 1
		elif action == "complete":
			statistics.completed_notes += 1

		session.commit()

		return False


def delete_file_deleted_note(path_file: str):
	os.remove(path_file)
