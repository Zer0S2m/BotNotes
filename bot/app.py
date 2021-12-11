import asyncio

from aiogram import Dispatcher
from aiogram import Bot
from aiogram.types import BotCommand

from handlers import handlers

from dispatcher import dp
from dispatcher import bot

from state import StatesCreateNote
from state import StatesCreateCategory


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command = "/info", description = "Инфо о создание записи"),
        BotCommand(command = "/note", description = "Управление записями"),
        BotCommand(command = "category", description = "Управление категориями"),
    ]

    await bot.set_my_commands(commands)


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(handlers.process_start_command, commands = ['start'])
	dp.register_message_handler(handlers.process_help_command, commands = ["help"])
	dp.register_message_handler(handlers.process_info_command, commands = ["info"])
	dp.register_message_handler(handlers.process_note_control, commands = ["note"])
	dp.register_message_handler(handlers.process_category_control, commands = ["category"])

	dp.register_callback_query_handler(handlers.process_create_note, lambda c: c.data == 'create_note')
	dp.register_callback_query_handler(handlers.process_view_note, lambda c: c.data == 'view_note')
	dp.register_callback_query_handler(handlers.process_create_category, lambda c: c.data == 'create_category')
	dp.register_callback_query_handler(handlers.process_view_category, lambda c: c.data == 'view_category')

	dp.register_message_handler(handlers.process_create_note_title_state, state = StatesCreateNote.STATE_CREATE_NOTE_TITLE)
	dp.register_message_handler(handlers.process_create_note_text_state, state = StatesCreateNote.STATE_CREATE_NOTE_TEXT)
	dp.register_message_handler(handlers.process_create_note_category_state, state = StatesCreateNote.STATE_CREATE_NOTE_CATEGORY)
	dp.register_message_handler(handlers.process_create_category_state, state = StatesCreateCategory.STATE_CREATE_CATEGORY)


async def main():
	register_handlers(dp = dp)
	await set_commands(bot = bot)

	await dp.start_polling()


if __name__ == '__main__':
	asyncio.run(main())
