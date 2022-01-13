from aiogram.utils.helper import (
	Helper, HelperMode, ListItem
)

from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup


class FSMFormNote(StatesGroup):
	"""Состояние для создания записи"""

	title = State()
	text = State()
	category = State()
	date_completion = State()
	file_download = State()


class FSMFormCategory(StatesGroup):
	"""Состояние для создания категории"""

	title = State()


class StatesNote(Helper):
	"""Состояние для управление над записями"""

	mode = HelperMode.snake_case

	STATE_VIEW_NOTE_ON_CATEGORY = ListItem()
	STATE_VIEW_NOTE_ON_DATE = ListItem()


class StatesCategory(Helper):
	"""Состояние для управление над категориями"""

	mode = HelperMode.snake_case

	STATE_DELETE_CATEGORY = ListItem()
