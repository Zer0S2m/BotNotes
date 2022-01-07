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
	dp.register_message_handler(common.process_start_command, commands = ['start'], state = "*")
	dp.register_message_handler(common.process_help_command, commands = ["help"])
	dp.register_message_handler(common.process_info_command, commands = ["info"])
	dp.register_message_handler(note.process_note_control, commands = ["note"])
	dp.register_message_handler(category.process_category_control, commands = ["category"])
	dp.register_message_handler(statistics.process_statistics_control, commands = ["statistics"])
	dp.register_message_handler(common.cmd_cancel, commands = ["cancel"], state = "*")
	dp.register_message_handler(common.cmd_cancel, Text(equals = "отмена", ignore_case = True), state = "*")

	note.reqister_handler_note()
	category.reqister_handler_category()


async def main():
	register_handlers(dp = dp)
	await set_commands(bot = bot)

	await dp.start_polling()


if __name__ == '__main__':
	asyncio.run(main())
