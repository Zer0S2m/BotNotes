TOKEN = ""
NAME_DB = "db_bot"

LIMIT_TITLE = 255
LIMIT_CATEGORY = 255
LIMIT_TEXT = 1000

INFO_TEXT = "Для получения информации воспользуйтесь командой: /info"

MESSAGES = {
	"start": f"""
		Привет!
		Веду твой список дел!\n
		/help - всевозможные команды
	""".replace('\t', ''),
	"help": """
		Веду твой список дел!\n
		/note - управление заметками
		/category - управление категориями
		/info - информация о создании заметки
	""".replace('\t', ''),
	"info": f"""
		Информация о создание записи!\n\n
		Заголовок для записи <u>необязателен</u>, но описание <u>должно присуствовать</u>.\n
		Максимальное количество символов у заголовка: <b>{LIMIT_TITLE}</b>.\n
		Максимальное количество символов у описания: <b>{LIMIT_TEXT}</b>.
		Максимальное количество символов у названия категории: <b>{LIMIT_CATEGORY}</b>.
		Заголовок категории не <u>должно начинаться</u> с <b>символов</b> или каких-либо <b>знаков</b>.\n
		Для отмены введения заголовка или выбора категории при создании записи, введите следующее значение: -
	""".replace('\t', ''),
}
