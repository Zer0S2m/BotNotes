from aiogram.utils.helper import (
	Helper, HelperMode, ListItem
)


class StatesCreateNote(Helper):
	"""docstring for StatesCreateNote"""

	mode = HelperMode.snake_case

	STATE_CREATE_NOTE_TITLE = ListItem()
	STATE_CREATE_NOTE_TEXT = ListItem()
	STATE_CREATE_CATEGORY = ListItem()
