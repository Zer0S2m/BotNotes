from aiogram.utils.helper import (
	Helper, HelperMode, ListItem
)

from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup


class FSMFormNote(StatesGroup):
	"""docstring for FSMFormNote"""

	title = State()
	text = State()
	category = State()


class FSMFormCategory(StatesGroup):
	"""docstring for FSMFormCategory"""

	title = State()


class StatesNote(Helper):
	"""docstring for StatesNote"""

	mode = HelperMode.snake_case

	STATE_VIEW_NOTE_ON_CATEGORY = ListItem()
