from models import (
	User, Note, Category
)

from dispatcher import session


def add_db_new_note(data, username):
	new_note = Note(
		text = data["text"],
		user_id = session.query(User).filter(User.username == username).first().id
	)

	if data["title"]:
		new_note.title = data["title"]

	if data["category"]:
		new_note.category_id = data["category"]

	session.add(new_note)
	session.commit()


def create_text_note(note):
	pub_date = get_pub_date_note(date = session.query(Note).first().pub_date)
	text = f"<b>Описание</b> - {note.text}"

	if str(note.title)[0] != "0" and len(note.title) > 0:
		text = f"<b>Заголовок</b> - {note.title}\n\n{text}"

	if note.category_id:
		text += f"\n\n<b>Категория</b> - {session.query(Category).filter(Category.id == note.category_id).first().title}"

	text += f"\n\n{pub_date}"

	return text


def get_pub_date_note(date):
	return f'{date.strftime("%d.%m.%Y")} {date.strftime("%H:%M")}'
