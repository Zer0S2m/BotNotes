import asyncio

from aiogram import Dispatcher
from aiogram import Bot
from aiogram.types import BotCommand
from aiogram.dispatcher.filters import Text

from handlers import (
	common, note, category,
	statistics
)

from dispatcher import dp
from dispatcher import bot

from state import (
	StatesNote, FSMFormCategory, FSMFormNote,
	StatesCategory
)


async def set_commands(bot: Bot):
	commands = [
		BotCommand(command = "/info", description = "Инфо о создание записи"),
		BotCommand(command = "/note", description = "Управление записями"),
		BotCommand(command = "/category", description = "Управление категориями"),
		BotCommand(command = "/statistics", description = "Статистика"),
		BotCommand(command = "/cancel", description = "Отмена команды"),
	]

	await bot.set_my_commands(commands)


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(common.process_start_command, commands = ['start'], state="*")
	dp.register_message_handler(common.process_help_command, commands = ["help"])
	dp.register_message_handler(common.process_info_command, commands = ["info"])
	dp.register_message_handler(note.process_note_control, commands = ["note"])
	dp.register_message_handler(category.process_category_control, commands = ["category"])
	dp.register_message_handler(statistics.process_statistics_control, commands = ["statistics"])
	dp.register_message_handler(common.cmd_cancel, commands = ["cancel"], state="*")
	dp.register_message_handler(common.cmd_cancel, Text(equals = "отмена", ignore_case = True), state = "*")

	dp.register_callback_query_handler(note.process_create_note, lambda c: c.data == 'create_note')
	dp.register_callback_query_handler(note.process_delete_note, text_contains = 'delete_note_')
	dp.register_callback_query_handler(note.process_complete_note, text_contains = 'complete_note_')
	dp.register_callback_query_handler(note.process_view_note, lambda c: c.data == 'view_note')
	dp.register_callback_query_handler(note.process_view_note_on_category, lambda c: c.data == 'view_note_on_category')
	dp.register_callback_query_handler(category.process_create_category, lambda c: c.data == 'create_category')
	dp.register_callback_query_handler(category.process_delete_category, lambda c: c.data == 'delete_category')
	dp.register_callback_query_handler(category.process_view_category, lambda c: c.data == 'view_category')

	dp.register_message_handler(note.process_create_note_title_state, state = FSMFormNote.title)
	dp.register_message_handler(note.process_create_note_text_state, state = FSMFormNote.text)
	dp.register_message_handler(note.process_create_note_category_state, state = FSMFormNote.category)
	dp.register_message_handler(note.process_view_note_on_category_state, state = StatesNote.STATE_VIEW_NOTE_ON_CATEGORY)
	dp.register_message_handler(category.process_create_category_state, state = FSMFormCategory.title)
	dp.register_message_handler(category.process_delete_category_state, state = StatesCategory.STATE_DELETE_CATEGORY)


async def main():
	register_handlers(dp = dp)
	await set_commands(bot = bot)

	await dp.start_polling()


if __name__ == '__main__':
	asyncio.run(main())
