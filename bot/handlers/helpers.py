import re
import datetime

from models import (
	User, Note, Category,
	Statistics
)

from dispatcher import session


def add_db_new_note(data: dict, username: str):
	user_id = session.query(User).filter(User.username == username).first().id
	new_note = Note(
		text = data["text"],
		user_id = user_id
	)

	if "title" in data:
		new_note.title = data["title"]

	if "category" in data:
		new_note.category_id = data["category"]

	if ("number_day" in data) and ("number_month" in data) and ("number_year" in data):
		complete_date = datetime.date(data["number_year"], data["number_month"], data["number_day"])
		new_note.complete_date = complete_date

	session.add(new_note)

	statistics = session.query(Statistics).filter_by(user_id = user_id).first()
	statistics.total_notes += 1

	session.commit()


def create_text_note(note: Note) -> str:
	pub_date = get_pub_date_note(
		date = session.query(Note).filter(Note.id == note.id).first().pub_date
	)
	text = f"<b>Описание</b> - {note.text}"

	if str(note.title)[0] != "0" and len(note.title) > 0:
		text = f"<b>Заголовок</b> - {note.title}\n{text}"

	if note.category_id:
		text += f"\n\n<b>Категория</b> - {session.query(Category).filter(Category.id == note.category_id).first().title}"

	if str(note.complete_date)[0] != "0" and len(note.complete_date) > 0:
		complete_date_split = list(map(int, note.complete_date.split("-")))
		complete_date = get_pub_date_note(date = datetime.datetime(*complete_date_split))
		complete_date = re.sub(r"\s\d{0,2}:\d{0,2}", "", complete_date)

		text += f"\n\n<b>Дата завершения</b> - {complete_date}"

	text += f"\n\n{pub_date}"

	return text


def get_pub_date_note(date: datetime.datetime) -> str:
	return f'{date.strftime("%d.%m.%Y")} {date.strftime("%H:%M")}'


def delete_note(username: str, data: str, action: str):
	user_id = session.query(User).filter(User.username == username).first().id
	note_id = re.search(r"\d{1,10}", data).group(0)

	note_deleted = session.query(Note).filter_by(
		user_id = user_id, id = note_id
	).first()

	session.delete(note_deleted)

	statistics = session.query(Statistics).filter_by(user_id = user_id).first()

	if action == "delete":
		statistics.unfinished_notes += 1
	elif action == "complete":
		statistics.completed_notes += 1

	session.commit()
