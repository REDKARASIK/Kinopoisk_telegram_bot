from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp


async def start(update, context):
    keyboard = [[InlineKeyboardButton("Поиск фильма", callback_data='search'),
                 InlineKeyboardButton("Оценки фильмов", callback_data='assessments')],
                [InlineKeyboardButton("Мои фильмы", callback_data='my_movies'),
                 InlineKeyboardButton("Подборки", callback_data='mixes')],
                [InlineKeyboardButton("Рандом", callback_data='random')]
                ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Добро пожаловать в стартовое меню бота.\nЗдесь вы можете найти нужную вам функцию.", reply_markup=reply_markup)


async def button(update, context):
    query = update.callback_query
    await query.answer()
    print(query.data)
    await query.edit_message_text(f"Вы нажали {query.data}")


async def search_film(update, context):
    keyboard = [[InlineKeyboardButton('Поиск фильмов по названию', callback_data='search_by_name'),
                 InlineKeyboardButton('Поиск фильмов по актёру', callback_data='search_by_actor')],
                [InlineKeyboardButton('Поиск по фильмов по режиссёру', callback_data='search_by_director'),
                 InlineKeyboardButton('Поиск фильмов по жанру', callback_data='search_by_genre')],
                [InlineKeyboardButton('Назад', callback_data='start')]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Вы можете найти фильмы, по заданным вами параметрам.', reply_markup=markup)
