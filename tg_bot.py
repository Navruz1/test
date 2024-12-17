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

# если код верификации верный, то сохраняет статус verified и спрашивает локацию
async def check_code(message: types.Message):
    user_id = message.from_user.id
    language = user_data[user_id]["language"]
    code = message.text
    verification_code = user_data[user_id]["verification_code"]
    if code == verification_code:
        user_data[user_id]["status"] = "verified"
        bot_answer = answers[language][4] #Номер подтверждён
        del user_data[user_id]["verification_code"]
        print(user_data)
        await message.answer(bot_answer)
        await ask_location(message)
    else:
        bot_answer = answers[language][5] #Неверный код. Попробуйте снова
        await message.answer(bot_answer)

# сохраняет локацию в user_data и выводит главное меню
async def ask_location(message : types.Message):
    user_id = message.from_user.id
    if "location" in user_data[user_id]:
        del user_data[user_id]["location"]
    if "holat" in user_data[user_id]:
        del user_data[user_id]["holat"]
    button = [
        [types.KeyboardButton(text="Отправить локацию", request_location=True)]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True)
    await message.answer("Укажите свою локацию", reply_markup=keyboard)

async def info_location(message : types.Message):
    user_id = message.from_user.id
    if "location" not in user_data[user_id]:
        if message.location is not None:
            latitude = message.location.latitude
            longitude = message.location.longitude
            location = {
                'latitude' : latitude,
                'longitude' : longitude
            }
        else:
            location = message.text
        user_data[user_id]['location'] = location
    button = [
        [types.KeyboardButton(text="Сделать заказ")],
        [types.KeyboardButton(text="Назад")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True)
    user_data[user_id]["holat"] = "kategoriyalar"
    await message.answer("Начали?", reply_markup=keyboard)
    print(user_data)

menu = {
    "Бургеры" : {"Чизбургер" : 27000, "Чилибургер" : 26000, "Гамбургер" : 25000},
    "Курочка" : {"Крылышки" : 30000, "Куриные ножки" : 200, "Стрипс" : 300},
    "Напитки" : {"Ice-Tea" : 17000, "Чай" : 4000, "Кола" : 17000}
}

async def show_menu(message : types.Message):
    user_id = message.from_user.id
    user_data[user_id]["holat"] = "tovarlar"
    if message.text == "Сделать заказ" or "tovar" in user_data[user_id]["holat"]:
        if "basket" not in user_data[user_id]:
            user_data[user_id]["basket"] = {}
        buttons = []
        for category in menu:
            button = [types.KeyboardButton(text=category)]
            buttons.append(button)
        button_back = [types.KeyboardButton(text="Назад")]
        buttons.append(button_back)
        keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        await message.answer("Выберите категорию", reply_markup=keyboard)
        print(user_data)
    elif message.text == "Назад":
        await ask_location(message)

async def check_menu(message : types.Message):
    user_id = message.from_user.id
    category = message.text
    user_data[user_id]["holat"] = "tovar"
    if category in menu:
        user_data[user_id]["category"] = category
        await show_items(message)
    elif category == "Назад":
        await info_location(message)

async def show_items(message : types.Message):
    user_id = message.from_user.id
    category = user_data[user_id]["category"]
    buttons = []
    for item in menu[category]:
        button = [types.KeyboardButton(text=item)]
        buttons.append(button)
    button_back = [types.KeyboardButton(text="Назад")]
    buttons.append(button_back)
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    user_data[user_id]["holat"] = "tovar"
    await message.answer("Что закажете?", reply_markup=keyboard)
    print(user_data)

async def check_items(message : types.Message):
    user_id = message.from_user.id
    item = message.text
    category = user_data[user_id]["category"]
    if item in menu[category]:
        user_data[user_id]["item"] = item
        price = menu[category][item]
        buttons = [
            [types.InlineKeyboardButton(text=f"-", callback_data=f"minus_{item}"),
             types.InlineKeyboardButton(text=f"1", callback_data=f"count_{item}"),
             types.InlineKeyboardButton(text=f"+", callback_data=f"plus_{item}")],
            [types.InlineKeyboardButton(text=f"Добавить в корзину", callback_data=f"add_{item}")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(f"Товар: {item}\n"
                             f"Цена: {price} сум", reply_markup=keyboard)
        print(user_data)
    elif item == "Назад":
        await show_menu(message)



# InputMedia
# os - работа с проводником

count = 1
@dp.callback_query(lambda c: c.data.startswith(('plus', 'minus', 'add')))
async def check_callback_data(callback : types.CallbackQuery):
    user_id = callback.from_user.id
    command, item = callback.data.split("_")
    global count
    if command == "plus":
        count += 1
    elif command == "minus":
        if count > 1:
            count -= 1
    elif command == "add":
        if item in user_data[user_id]["basket"]:
            user_data[user_id]["basket"][item] += count
        else:
            user_data[user_id]["basket"][item] = count
        count = 1

        print(user_data)
    buttons = [
        [types.InlineKeyboardButton(text=f"-", callback_data=f"minus_{item}"),
         types.InlineKeyboardButton(text=f"{count}", callback_data=f"count_{item}"),
         types.InlineKeyboardButton(text=f"+", callback_data=f"plus_{item}")],
        [types.InlineKeyboardButton(text=f"Добавить в корзину", callback_data=f"add_{item}")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    category = user_data[user_id]["category"]
    price = menu[category][item]
    price = price * count
    try:
        await callback.message.edit_text(f"Товар: {item}\n"
                                         f"Цена: {price} сум", reply_markup=keyboard)
    except:
        pass
    print("Count:", count)



async def main():
    await dp.start_polling(bot)

print("The bot is running...")
asyncio.run(main())

