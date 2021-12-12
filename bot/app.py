import asyncio

from aiogram import Dispatcher
from aiogram import Bot
from aiogram.types import BotCommand

from handlers import common
from handlers import note
from handlers import category

from dispatcher import dp
from dispatcher import bot

from state import (
	StatesNote, FSMFormCategory, FSMFormNote
)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command = "/info", description = "Инфо о создание записи"),
        BotCommand(command = "/note", description = "Управление записями"),
        BotCommand(command = "/category", description = "Управление категориями"),
    ]

    await bot.set_my_commands(commands)


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(common.process_start_command, commands = ['start'])
	dp.register_message_handler(common.process_help_command, commands = ["help"])
	dp.register_message_handler(common.process_info_command, commands = ["info"])
	dp.register_message_handler(note.process_note_control, commands = ["note"])
	dp.register_message_handler(category.process_category_control, commands = ["category"])

	dp.register_callback_query_handler(note.process_create_note, lambda c: c.data == 'create_note')
	dp.register_callback_query_handler(note.process_view_note, lambda c: c.data == 'view_note')
	dp.register_callback_query_handler(note.process_view_note_on_category, lambda c: c.data == 'view_note_on_category')
	dp.register_callback_query_handler(category.process_create_category, lambda c: c.data == 'create_category')
	dp.register_callback_query_handler(category.process_view_category, lambda c: c.data == 'view_category')

	dp.register_message_handler(note.process_create_note_title_state, state = FSMFormNote.title)
	dp.register_message_handler(note.process_create_note_text_state, state = FSMFormNote.text)
	dp.register_message_handler(note.process_create_note_category_state, state = FSMFormNote.category)
	dp.register_message_handler(note.process_view_note_on_category_state, state = StatesNote.STATE_VIEW_NOTE_ON_CATEGORY)
	dp.register_message_handler(category.process_create_category_state, state = FSMFormCategory.title)


async def main():
	register_handlers(dp = dp)
	await set_commands(bot = bot)

	await dp.start_polling()


if __name__ == '__main__':
	asyncio.run(main())
