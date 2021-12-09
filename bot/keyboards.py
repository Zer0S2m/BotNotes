from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import KeyboardButton


button_hi = KeyboardButton('Привет! 👋')

greet_kb = ReplyKeyboardMarkup()
greet_kb.add(button_hi)