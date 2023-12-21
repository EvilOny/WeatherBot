import telebot
from Bot.data.config import TOKEN
from Bot.data.tools import send_welcome, alert_temperature, choice, location_geo, location_city, alert_turn_on, alert_city

bot = telebot.TeleBot(TOKEN, parse_mode=None)


@bot.message_handler(commands=['start'])
def welcome(message):
    send_welcome(message, bot)


@bot.message_handler(func=lambda message: message.text == 'Показать погоду на данный момент' or
                                          message.text == 'Показать прогноз погоды на 5 дней вперёд' or
                                          message.text == 'Настроить автоматические уведомления')
def user_choice(message):
    choice(message, bot)


@bot.message_handler(content_types=['location'])
def geolocation(message):
    location_geo(message, bot)


@bot.message_handler(func=lambda message: message.text == 'Включить оповещения' or
                                          message.text == 'Выключить оповещения')
def alert_on(message):
    alert_turn_on(message, bot)


@bot.message_handler(func=lambda message: message.text == 'Указать границы температур')
def alert_temp(message):
    alert_temperature(message, bot)


@bot.message_handler(func=lambda message: message.text == 'Указать город')
def city_alert(message):
    alert_city(message, bot)


@bot.message_handler(func=lambda message: message.text == 'Назад')
def back(message):
    send_welcome(message, bot)


@bot.message_handler(func=lambda message: True)
def cityloc(message):
    location_city(message, bot)


bot.infinity_polling()
