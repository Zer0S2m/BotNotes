import asyncio

from aiogram import Bot
from aiogram.types import BotCommand

from handlers import (
	common, note, category,
	statistics
)

from dispatcher import dp
from dispatcher import bot


async def set_commands(bot: Bot):
	commands = [
		BotCommand(command = "/info", description = "Инфо о создание записи"),
		BotCommand(command = "/note", description = "Управление записями"),
		BotCommand(command = "/category", description = "Управление категориями"),
		BotCommand(command = "/statistics", description = "Статистика"),
		BotCommand(command = "/cancel", description = "Отмена команды"),
	]

	await bot.set_my_commands(commands)


def register_handlers():
	common.reqister_handler_common()
	note.reqister_handler_note()
	category.reqister_handler_category()
	statistics.reqister_handler_statistics()


async def main():
	register_handlers()
	await set_commands(bot = bot)

	await dp.start_polling()


if __name__ == '__main__':
	asyncio.run(main())
