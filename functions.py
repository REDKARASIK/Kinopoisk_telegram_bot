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

    await update.message.reply_text("HELLO", reply_markup=reply_markup)


async def button(update, context):
    query = update.callback_query
    await query.answer()
    print(query.data)
    await query.edit_message_text(f"Вы нажали {query.data}")


