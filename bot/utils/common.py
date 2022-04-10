import os
import re
import datetime as DT
from typing import List

from aiogram import types

from dispatcher import bot

from config import (
	DATE, FILE_EXTENSION, STATIC_FILES
)

from models import Note


def set_title_category(title: str) -> str:
	return title.strip().lower()


def set_complete_date_note(data: dict) -> DT.date:
	return DT.date(data["number_year"], data["number_month"], data["number_day"])


def delete_file_local_storage(path_file: str):
	os.remove(path_file)


def get_note_id_from_btn_note(data: str) -> int:
	return int(re.search(r"\d{1,10}", data).group(0))


def get_pub_date_note(date: DT.datetime) -> str:
	return f'{date.strftime("%d.%m.%Y")} {date.strftime("%H:%M")}'


def set_choice_date_for_text(choice_date: DT.datetime) -> str:
	choice_date = get_pub_date_note(date = choice_date)
	choice_date = re.sub(r"\s\d{0,2}:\d{0,2}", "", choice_date)

	return choice_date


def set_choice_date(parse_date: dict) -> DT.datetime:
	return DT.datetime(
		int(parse_date["number_year"].group(1)),
		int(parse_date["number_month"].group(1)),
		int(parse_date["number_day"].group(1)),
		23, 59, 59
	)


def cleans_dict_date():
	DATE["day"] = DT.datetime.now().day
	DATE["month"] = DT.datetime.now().month
	DATE["year"] = DT.datetime.now().year


def parse_date_str(data: str) -> dict:
	number_day = re.search(r"day:(\d{0,2})", data)
	number_month = re.search(r"month:(\d{0,2})", data)
	number_year = re.search(r"year:(\d{0,4})", data)

	return {
		"number_day": number_day,
		"number_month": number_month,
		"number_year": number_year
	}


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


async def create_text_note(note: Note) -> dict:
	pub_date = get_pub_date_note(date = note.pub_date)

	text = f"<b>Описание</b> - {note.text}"

	if str(note.title)[0] != "0" and len(note.title) > 0:
		text = f"<b>Заголовок</b> - {note.title}\n{text}"

	if note.category:
		text += f"\n\n<b>Категория</b> - {note.category.title.title()}"

	if str(note.complete_date)[0] != "0" and len(note.complete_date) > 0:
		complete_date_split = list(map(int, note.complete_date.split("-")))
		complete_date = get_pub_date_note(DT.datetime(*complete_date_split))
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


def set_complete_date_update_note(data: dict) -> dict:
	if "complete_date" in data:
		if data["complete_date"] == "not":
			data["complete_date"] = "0"
			return data

		data["complete_date"] = set_complete_date_note({
			"number_year": data["complete_date"]["number_year"],
			"number_month": data["complete_date"]["number_month"],
			"number_day": data["complete_date"]["number_day"]
		})

	return data


def update_params_note_db(
	note: Note,
	data: dict
):
	for key, value in data.items():
		if key != "note_id" and key != "username" and key != "file":
			setattr(note, key, value)


def get_dates_periods(data: dict) -> List[DT.datetime]:
	dates = sorted([
		DT.datetime(*list(map(int, data["periods"]["first"].split("-")))),
		DT.datetime(*list(map(int, data["periods"]["second"].split("-"))))
	])

	dates[0] = dates[0] + DT.timedelta(hours = 0, minutes = 0, seconds = 0)
	dates[1] = dates[1] + DT.timedelta(hours = 23, minutes = 59, seconds = 59)

	return dates
