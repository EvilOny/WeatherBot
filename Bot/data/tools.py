from telebot import types
import requests
from Bot.data.config import API_KEY, GEO_URL, WEATHER_URL, FORECAST_URL
from matplotlib import pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Используемые переменные
on = False
upper = 30
lower = -30
flag = "upper"
alert_lat = 0
alert_lon = 0
chat_id = 0


# Функции, связанные с определением города
def geo(message, bot):
    """
    Функция вызывается при выборе местоположения и выводит клавиатуру с выбором действия
    Действия:
    - Ввести название города
    - Отправить местоположение (доступно для мобильного приложения)
    """
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
    markup.add(button_geo)
    bot.send_message(message.chat.id, "Нажми на кнопку и отправь своё местоположение или введи название города",
                     reply_markup=markup)


def city(message, bot):
    """
    Функция принимает на вход город от пользователя и возвращает долготу/широту
    """
    params = dict(q=message, appid=API_KEY, limit=1)
    response = requests.get(GEO_URL, params=params)
    data = response.json()
    lat = data[0]["lat"]
    lon = data[0]["lon"]
    return lat, lon


def location_geo(message, bot):
    """
    Функция обрабатывает геолокацию
    """
    if message.location is not None:
        if cmd == 'current':
            weather(message, message.location.latitude, message.location.longitude, bot)
        else:
            plot(message, message.location.latitude, message.location.longitude, bot)


def location_city(message, bot):
    """
    Функция отлавливает название города для вывода погоды
    """
    try:
        lat, lon = city(message.text, bot)
        if cmd == 'current':
            weather(message, lat, lon, bot)
        else:
            plot(message, lat, lon, bot)
    except:
        bot.send_message(message.chat.id, 'Вы ввели команду которую я не знаю')
        send_welcome(message, bot)


# Функции, отвечающие за непосредственный вывод погоды
def weather(message, lat, lon, bot):
    """
    Функция получает на вход широту и долготу
    Делает запрос к API
    В случае, если код страницы 200, то отправляем пользователю сообщение с погодой
    Иначе отправляем сообщение с ошибкой
    """
    params = dict(lat=lat, lon=lon, appid=API_KEY, units="metric", lang="ru")
    response = requests.get(WEATHER_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        response = (f'Прогноз погоды для города {data["name"]}\n') + \
                   (f'Температура воздуха: {data["main"]["temp"]} °C\n') + \
                   (f'Ощущается как: {data["main"]["feels_like"]} °C\n') + \
                   (f'Скорость ветра: {data["wind"]["speed"]} м/с\n') + \
                   (f'Направление ветра: {data["wind"]["deg"]} °\n') + \
                   (f'Давление: {data["main"]["pressure"]} мм рт. ст.\n') + \
                   (f'Влажность: {data["main"]["humidity"]} %\n') + \
                   (f'Погодное описание: {data["weather"][0]["main"]}')
    else:
        response = (f'Ошибка: {response.status_code}')
    bot.send_message(message.chat.id, response)
    send_welcome(message, bot)


def plot(message, lat, lon, bot):
    """
    Функция занимается прогнозированием и построением графика прогноза температуры на 5 дней
    """
    timestamps = []
    values = []
    global data
    params = dict(lat=lat, lon=lon, appid=API_KEY, units="metric")
    response = requests.get(FORECAST_URL, params=params)
    if response.status_code == 200:
        data = response.json()
    else:
        print("error")
    for i in range(40):
            timestamps.append(data["list"][i]["dt"])
            values.append(data["list"][i]["main"]["temp"])

    datetimes = [datetime.utcfromtimestamp(ts) for ts in timestamps]

    plt.figure(figsize=(10, 6))
    plt.plot(datetimes, values, marker='o')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S %d-%m-%y'))

    plt.gcf().autofmt_xdate()

    plt.xlabel('Время')
    plt.ylabel('Температура')
    plt.title('Прогноз температуры на ближайшие 5 дней в ' + data["city"]["name"])
    plt.grid(True)

    plt.savefig("plot.png")

    img = open("../plot.png", 'rb')

    bot.send_photo(message.chat.id, img)

    send_welcome(message, bot)


# Функции, отвечающие за мониторинг и уведомления
def borders(message, flag, bot):
    """
    Функция вызывается при выборе температурного диапазона
    """
    if flag == "lower":
        global lower
        lower = int(message.text)
        send_welcome(message, bot)
    else:
        global upper
        upper = int(message.text)
        alert_temperature(message, bot)


def alert_location(message, bot):
    """
    Функция отвечает за назначение широты и долготы города для мониторинга погоды
    """
    global alert_lat, alert_lon
    alert_lat, alert_lon = city(message.text, bot)
    send_welcome(message, bot)


def alert_setting(message, bot):
    """
    Функция вызывается при настройке автомотических уведомлений при мониторинге погоды
    Выводит пользователю клавиатуру с выбором
    """
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button1 = types.KeyboardButton('Указать границы температур')
    if on:
        button2 = types.KeyboardButton('Выключить оповещения')
    else:
        button2 = types.KeyboardButton('Включить оповещения')
    button3 = types.KeyboardButton('Указать город')
    button4 = types.KeyboardButton('Назад')
    markup.add(button1)
    markup.add(button2)
    markup.add(button3)
    markup.add(button4)
    bot.send_message(message.chat.id, "Текущие границы:\nВерхняя:" + str(upper) + "\nНижняя:" + str(lower),
                     reply_markup=markup)


def alert():
    """
    Функция делает запросы к API, проверяет находится ли температура в рамках установленной
    В случае, если она выше или ниже установленной, то пользователю отправляется уведомление
    """
    global on
    if on:
        params = dict(lat=alert_lat, lon=alert_lon, appid=API_KEY, units="metric")
        response = requests.get(WEATHER_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if int(lower) > int(data["main"]["temp"]):
                objBot.send_message(chat_id, 'Температура упала ниже заданной границы!')
                on = not on
            if int(data["main"]["temp"]) > int(upper):
                objBot.send_message(chat_id, 'Температура превысила заданную границу!')
                on = not on


def alert_temperature(message, bot):
    """
    Функция предлагает пользователю ввести нижнее и верхнее значение температур для мониторинга
    """
    global flag
    if flag == "lower":
        bot.send_message(message.chat.id, "Введите нижнюю границу температур")
        flag = "upper"
        bot.register_next_step_handler(message, borders, "lower", bot)
    else:
        bot.send_message(message.chat.id, "Введите верхнюю границу температур")
        flag = "lower"
        bot.register_next_step_handler(message, borders, "upper", bot)


def alert_turn_on(message, bot):
    """
    Функция вызывается при включении мониторинга погоды
    """
    global on
    global objBot
    global chat_id
    if (alert_lat and alert_lon) != 0:
        on = not on
        chat_id = message.chat.id
        objBot = bot
        scheduler.add_job(alert, 'interval', minutes=1)
        scheduler.start()
    else:
        bot.send_message(message.chat.id, 'Сперва укажите город')
    send_welcome(message, bot)


def alert_city(message, bot):
    """
    Функция предлагает пользователю ввести город для мониторинга погоды
    """
    bot.send_message(message.chat.id, 'Введите название города:')
    bot.register_next_step_handler(message, alert_location, bot)


# Функции, управления ботом
def send_welcome(message, bot):
    """
    Ожидает /start от пользователя и выводит клавиатуру с выбором действия
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Показать погоду на данный момент')
    markup.add('Показать прогноз погоды на 5 дней вперёд')
    markup.add('Настроить автоматические уведомления')
    bot.send_message(message.chat.id, "Привет! Я погодный бот. Чем могу помочь?", reply_markup=markup)


def choice(message, bot):
    """
    Получает на вход сообщение с выбранным действием и вызывает функцию, которая отвечает за это действие
    """
    global cmd
    if message.text == 'Показать погоду на данный момент':
        geo(message, bot)
        cmd = 'current'
    elif message.text == 'Показать прогноз погоды на 5 дней вперёд':
        geo(message, bot)


        cmd = 'forecast'
    elif message.text == 'Настроить автоматические уведомления':
        alert_setting(message, bot)
    else:
        bot.send_message(message.chat.id, 'Вы ввели команду которую я не знаю')
        send_welcome(message, bot)
