import asyncio
import requests # (для отправки смс)
# import io

from aiogram import types, Bot, Dispatcher
from aiogram.filters import Command
from random import randint

TOKEN = "7644799185:AAHEFF2mvXWl5plIzPtb9m04SgPzJgCudTA"
channel_name = "ustudy_navruz_channel"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

# смс через шлюз сервиса eskiz.uz
email = "xaitboev.navruzbek@gmail.com"
password = "pj6Qd9wfQcivSP39OlXC3LK2cmsoPadQ8GWFz0wH"

def login_and_token(email, password):
    url = "https://notify.eskiz.uz/api/auth/refresh"
    payload = {
        "email": email,
        "password": password
    }
    files = []
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    if response.status_code == 200: # status code 200 - это антипод "404" ("страница не найдена")
        token = response.json()["data"]["token"]  # .json() превращает объект в словарь
        return token

def send_sms(token, phone):
    import requests
    url = "https://notify.eskiz.uz/api/message/sms/send"
    payload = {'mobile_phone': phone,
               'message': 'Eskiz Test',
               'from': '4546',
               'callback_url': 'http://0000.uz/test.php'}
    files = []
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    if response.status_code != 200:
        raise "Возникла ошибка"


answers = {
    "Русский" : [
        "Здравствуйте! Добро пожаловать в службу доставки Les Ailes", #0
        "Пожалуйста, введите свой телефон номер телефона", #1
        "Отправить номер", #2
        "Введите код верификации, отправленный на ваш номер\n\nКод верификации: ", #3
        "Номер подтверждён", #4
        "Неверный код. Попробуйте снова", #5
        "", #6
    ],
    "O'zbekcha" : [
        "Assalomu alaykum! Les Ailes yetkazib berish xizmatiga xush kelibsiz",
        "Iltimos, telefon raqamingizni kiriting",
        "Raqamni jo'natish",
        "Raqamingizga jo'natilgan texshiruv kodni kirriting\n\nTexshiruv kod:",
    ],
    "English" : [
        "Hello! Welcome to Les Ailes delivery service",
        "Please enter your phone number",
        "Enter the number",
        "Enter the verification code sent to your number",
    ]
}

@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data or message.text == "/start":
        await start(message)
    elif "language" not in user_data[user_id]:
        await send_number(message)
    elif "phone" not in user_data[user_id]:
        await send_code(message)
    elif "status" not in user_data[user_id]:
        await check_code(message)
    elif "location" not in user_data[user_id]:
        await info_location(message)
    elif "kategoriyalar" in user_data[user_id]["holat"]:
        await show_menu(message)
    elif "tovarlar" in user_data[user_id]["holat"]:
        await check_menu(message)
    elif "tovar" in user_data[user_id]["holat"]:
        await check_items(message)

# Спрашивает язык и вводит ответ в user_data
@dp.message(Command("start"))  # вызвать функцию на следующей строке
async def start(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    buttons = [
        [types.KeyboardButton(text="Русский"),
        types.KeyboardButton(text="O'zbekcha"),
        types.KeyboardButton(text="English")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer(f"{answers["Русский"][0]}\n\n"
                         f"{answers["O'zbekcha"][0]}\n\n"
                         f"{answers["English"][0]}", reply_markup=keyboard)
    print(user_data)

# спрашивает номер
async def send_number(message: types.Message):
    user_id = message.from_user.id
    language = message.text
    user_data[user_id]["language"] = language
    print(user_data)
    bot_answer = answers[language][2] #Отправить номер
    button = [
        [types.KeyboardButton(text=bot_answer, request_contact=True)]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True)
    bot_answer = answers[language][1] # Пожалуйста, введите свой телефон номер телефона
    await message.answer(bot_answer, reply_markup=keyboard)

# сохраняет номер в user_data, генерирует и сохраняет код верификации и спрашивает его
async def send_code(message: types.Message):
    user_id = message.from_user.id
    language = user_data[user_id]["language"]
    if message.contact is not None:
        phone = message.contact.phone_number
    else:
        phone = message.text
    ok = True
    if len(phone) == 12 or len(phone) == 13:
        if phone[0:4] == "+998" or phone[0:3] == "998":
            for num in phone:
                if num not in "+0123456789":
                    ok = False
                    break
        else:
            ok = False
    else:
        ok = False
    if ok:
        user_data[user_id]["phone"] = phone
        try:
            token = login_and_token(email, password)
            send_sms(token, phone)
            await message.answer("Введите код верификации, отправленный на ваш номер")
        except:
            await message.answer("Возникла ошибка при отправке смс")

        verification_code = str(randint(10, 99))
        user_data[user_id]["verification_code"] = verification_code
        print(user_data)
        bot_answer = answers[language][3]  # Введите код верификации, отправленный на ваш номер
        await message.answer(bot_answer + verification_code)
    else:
        await message.answer("Error number!")

