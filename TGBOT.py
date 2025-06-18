import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import gspread
import os
from dotenv import load_dotenv
load_dotenv()
import json
from google.oauth2.service_account import Credentials

import os
TOKEN = os.environ["BOT_TOKEN"]
GOOGLE_MAPS_LINK = "https://maps.app.goo.gl/wsAj7p5Fb8FtcRWa7"
SPREADSHEET_ID = "1syQja7ntuuv1mGP8BOapb0W1b8wTrV7Zce2ZOHnr4Ho"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню (ReplyKeyboard)
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Аренда Автомобилей"), KeyboardButton(text="Аренда Байков")],
        [KeyboardButton(text="Другие услуги"), KeyboardButton(text="Онлайн Менеджер")],
        [KeyboardButton(text="Цены и Каталог"), KeyboardButton(text="Где мы находимся")]
    ],
    resize_keyboard=True
)

def get_credentials():
    return Credentials.from_service_account_file(
        os.environ["CREDENTIALS_FILE"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )

def load_bikes_from_sheet():
    credentials = get_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(SPREADSHEET_ID).worksheet("Bike")
    data = sheet.get_all_values()
    rows = data[1:]  # Пропускаем заголовки


    bikes = {}
    for row in rows:
        if len(row) < 4:
            continue
        try:
            num = int(row[0])
        except ValueError:
            continue
        bikes[num] = {
            "name": row[1],
            "price": row[2],
            "photo": row[3],
            "description": ""
        }
    return bikes

# Подгружаем байки из Google Sheets
bikes = load_bikes_from_sheet()

# Заглушка для авто (будет позже)
cars = {
    1: {"name": "Toyota Corolla", "price": "1500 THB/день", "photo": "https://example.com/car1.jpg", "description": "Автомат, кондиционер"},
    2: {"name": "Honda Civic", "price": "1700 THB/день", "photo": "https://example.com/car2.jpg", "description": "Автомат, кожаный салон"},
}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Добро пожаловать! Выберите опцию:", reply_markup=main_kb)

@dp.message(lambda message: message.text == "Аренда Байков")
async def rent_bikes_handler(message: types.Message):
    photo_url = "https://i.ibb.co/5Vnppdt/photo-2024-12-30-09-15-13.jpg"  # Замени на настоящее общее фото байков
    await bot.send_photo(message.chat.id, photo_url, caption="Выберите байк по номеру:")

    builder = InlineKeyboardBuilder()
    for num in bikes:
        builder.button(text=str(num), callback_data=f"bike_{num}")
    builder.button(text="Где мы находимся", url=GOOGLE_MAPS_LINK)
    builder.button(text="Назад", callback_data="back_to_main")
    builder.adjust(5)
    await message.answer("Нажмите номер модели:", reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data and c.data.startswith("bike_"))
async def process_callback_bike(callback: types.CallbackQuery):
    _, num_str = callback.data.split("_")
    num = int(num_str)
    model = bikes.get(num)

    if not model:
        await callback.answer("Байк не найден.", show_alert=True)
        return

    text = f"🏍️ {model['name']}\n💰 Цена: {model['price']}"
    await bot.send_photo(callback.message.chat.id, model["photo"], caption=text)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery):
    await bot.send_message(callback.message.chat.id, "Главное меню:", reply_markup=main_kb)
    await callback.answer()

@dp.message(lambda message: message.text == "Где мы находимся")
async def location_handler(message: types.Message):
    await message.answer(f"Мы находимся тут: {GOOGLE_MAPS_LINK}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
