from datetime import datetime as DT


TOKEN = "5017770138:AAGbqEfqc_PV_StaQ7maaSvqazY_fByvbuU"
NAME_DB = "db_bot"

LIMIT_TITLE = 255
LIMIT_CATEGORY = 255
LIMIT_TEXT = 1000

STATIC_FILES = "static"
INFO_TEXT = "Для получения информации воспользуйтесь командой: /info"

FILE_EXTENSION = {
	"doc": "doc",
	"photo": "photo",
	"audio": "audio"
}

MESSAGES = {
	"start": """
		Привет {name}!
		Веду твой список дел!\n
		/help - всевозможные команды
	""".replace('\t', ''),
	"help": """
		Веду твой список дел!\n
		/note - управление заметками
		/category - управление категориями
		/info - информация о создании заметки
		/statistics - статистика
		/cancel - отмена команды
	""".replace('\t', ''),
	"info": f"""
		Информация о создание записи!\n\n
		Заголовок для записи <u>необязателен</u>, но описание <u>должно присуствовать</u>.\n
		Максимальное количество символов у заголовка: <b>{LIMIT_TITLE}</b>.\n
		Максимальное количество символов у описания: <b>{LIMIT_TEXT}</b>.
		Максимальное количество символов у названия категории: <b>{LIMIT_CATEGORY}</b>.
		Заголовок категории не <u>должен начинаться</u> с <b>символов</b> или каких-либо <b>знаков</b>.\n
		Для отмены введения заголовка, выбора категории или загрузки файла, при создании записи, введите следующее значение: <b>-</b>\n
		Для завершения редактирования заметки, введите следующее значение: <b>+</b>
	""".replace('\t', ''),
	"statistics": """
		<b>Статистика</b>\n
		Всего заметок: <b>{total_notes}</b>
		Завершённых заметок: <b>{completed_notes}</b>
		Незавершённых заметок: <b>{unfinished_notes}</b>
	""".replace('\t', ''),
}

DATE = {
	"day": DT.now().day,
	"month": DT.now().month,
	"year": DT.now().year,
}

MONTHS = {
	"1": "Январь",
	"2": "Февраль",
	"3": "Март",
	"4": "Апрель",
	"5": "Май",
	"6": "Июнь",
	"7": "Июль",
	"8": "Август",
	"9": "Сентябрь",
	"10": "Октябрь",
	"11": "Ноябрь",
	"12": "Декабрь",
}

PARAMS_EDIT = {
	"заголовок": "title",
	"категория": "category_id",
	"описание": "text",
	"файл": "file",
	"дата_завершения": "complete_date"
}
