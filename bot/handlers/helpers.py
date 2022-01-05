import re

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

	if data["title"]:
		new_note.title = data["title"]

	if data["category"]:
		new_note.category_id = data["category"]

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

	text += f"\n\n{pub_date}"

	return text


def get_pub_date_note(date: str) -> str:
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
