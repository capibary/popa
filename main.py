from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import datetime
import requests
from aiogram.utils import executor
import  os
bot = Bot(token=str(os.environ.get("TOK")))

dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


class Status(Helper):
    mode = HelperMode.snake_case
    STATE_1 = ListItem()


ApiKey = '688b588d9d56ba800218ae7f86cf55d2'


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    start_message = 'Привет, я бог погоды - Догода. \n' \
                    'Я могу тебе показать погоду в почти всех городах мира.\n' \
                    'Чтобы узнать как это сделать, напиши: /info'
    button_info = KeyboardButton('/info')
    greet_kb1 = ReplyKeyboardMarkup(resize_keyboard=True).add(button_info)
    await bot.send_message(message.chat.id, start_message, reply_markup=greet_kb1)


@dp.message_handler( commands=['info'])
async def info(message):
    info_message = 'Чтобы узнать погоду сначала напиши: /weather (обязательно), а потом город, в котором нужна ' \
                   'погода, можно уточнить, указав через запятую, идентификатор ' \
                   'страны, где этот город находится. Это желательно сделать, потому что по всему миру ' \
                   'может быть несколько городов с таким названием.\n' \
                   'Примеры правильного ввода: Moscow; Лондон, GB; Санкт-Петербург; Нью-Йорк.\n' \
                   'Снизу появится клавиатура с большими городами, чтобы не писать их.\n' \
                   '(картинка подбирается под состояние погоды)'
    markup_reply_info = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_reply_info.add('/weather')
    await bot.send_message(message.chat.id, info_message, reply_markup=markup_reply_info)


@dp.message_handler( commands=['weather'])
async def weather_step1(message):
    state = dp.current_state(user=message.chat.id)
    print(message)
    weather_message = 'Напишите город, в соответствии с правилами в info'
    markup_reply_cities = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_reply_cities.add('Москва, RU', 'Санкт-Петербург, RU')
    markup_reply_cities.add('Лондон, GB', 'Вашингтон, US')
    markup_reply_cities.add('Париж, FR', 'Прага, CZ')
    markup_reply_cities.add('Берлин, DE', 'Токио, JP')
    markup_reply_cities.add('Пекин, CN', 'Нью-Дели, IN')
    await bot.send_message(message.chat.id, weather_message, reply_markup=markup_reply_cities)
    await state.set_state(Status.all()[0])


@dp.message_handler(state=Status.STATE_1)
async def weather_step2(message):
    city = message.text
    info = requests.get('http://api.openweathermap.org/data/2.5/find',
                        params={'q': city, 'type': 'like', 'units': 'metric', 'lang': 'ru', 'APPID': ApiKey})
    data = info.json()
    try:
        city_id = data['list'][0]['id']
        weather = requests.get('http://api.openweathermap.org/data/2.5/weather',
                               params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': ApiKey})
        data = weather.json()
        time = str(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=data['timezone'] / 3600)))).split()
        main_message = f"{data['name']}, {data['sys']['country']}\n" \
                       f"Дата: {'.'.join(time[0].split('-')[::-1])} ⏱\n" \
                       f"Время: {time[1][:-13]}, UTC{time[1][-6:]} 🕟\n" \
                       f"Состояние погоды: {data['weather'][0]['description'].capitalize()} 🌏\n" \
                       f"🌡Температура: {data['main']['temp']}°,\nощущается как {data['main']['feels_like']}°🌡\n" \
                       f"Скорость ветра: {data['wind']['speed']} м/с 💨\n" \
                       f"Влажность: ~{data['main']['humidity']}% 💧"
        d_icon = data["weather"][0]["icon"]
        markup_reply_weather = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_reply_weather.add('/weather')
        await bot.send_photo(message.chat.id, f"http://openweathermap.org/img/wn/{d_icon}@2x.png",
                             caption=main_message, )
        await bot.send_message(message.chat.id, 'Сообщение, чтобы снова написать\n/weather (если надо)',
                               reply_markup=markup_reply_weather)
        markup_reply_weather = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_reply_weather.add('/weather')
        state = dp.current_state(user=message.from_user.id)
        await state.finish()
    except LookupError:
        error_message = 'К сожалению, я не нашел такого города. Возможны два варианта: 1) Вы неправильно ввели ' \
                        'город, который ищете; 2) Вы ищете очень малопопулярный город, которого нет в системе, ' \
                        'но это почти невозможно, 1 вариант куда более вероятен, поэтому перепроверте ввод и введите' \
                        'город ещё раз.'
        await bot.send_message(message.chat.id, error_message)

@dp.message_handler(content_types=['text', 'voice', 'audio', 'document', 'photo', 'sticker', 'video', 'location'])
async def notcommand(message):
    print(message)
    notcommand_message = 'Напишите команду /start, /info или /weather, все остальное я не понимаю.'
    await bot.send_message(message.chat.id, notcommand_message)
executor.start_polling(dp)
