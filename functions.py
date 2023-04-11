import logging
from pprint import pprint

import aiohttp
import telegram.error
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import API_KEY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    if 'chat_id' not in context.user_data:
        context.user_data['chat_id'] = update.message.chat_id
    keyboard = [[InlineKeyboardButton("Поиск фильма", callback_data='search'),
                 InlineKeyboardButton("Оценки фильмов", callback_data='assessments')],
                [InlineKeyboardButton("Мои фильмы", callback_data='my_movies'),
                 InlineKeyboardButton("Подборки", callback_data='mixes')],
                [InlineKeyboardButton("Рандом", callback_data='random')]
                ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(text=
                                   "Добро пожаловать в стартовое меню бота.\nЗдесь вы можете найти нужную вам функцию.",
                                   chat_id=context.user_data['chat_id'], reply_markup=reply_markup)


async def button(update, context):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        print(query.data)
        context.user_data['query_data'] = query.data
        if query.data == 'search':
            await search_film(query, context)
        if query.data == 'search_by_name':
            await search_by_name(query, context)
        if query.data == 'random':
            await random(query, context)
            await query.delete_message()
        if query.data == 'delete_random':
            await start(update, context)

    else:
        if 'query_data' in context.user_data:
            print(update.message.text, context.user_data['query_data'])


async def search_film(query, context):
    keyboard = [[InlineKeyboardButton('По названию', callback_data='search_by_name'),
                 InlineKeyboardButton('По актёру', callback_data='search_by_actor')],
                [InlineKeyboardButton('По режиссёру', callback_data='search_by_director'),
                 InlineKeyboardButton('По жанру', callback_data='search_by_genre')],
                [InlineKeyboardButton('Назад', callback_data='start')]]
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('Вы можете найти фильмы, по заданным вами параметрам.', reply_markup=markup)


async def get_response(url, params={}, headers={}):
    logger.info(f"getting {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            return await resp.json()


async def random(query, context):
    uri = 'https://api.kinopoisk.dev/v1/movie/random'
    response = await get_response(uri, headers={'X-API-KEY': API_KEY})
    pprint(response)
    text, img = parser_film(response)
    chat_id = context.user_data['chat_id']
    keyboard = [[InlineKeyboardButton('Назад', callback_data='delete_random')]]
    markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.send_photo(chat_id, img['url'], caption=text, reply_markup=markup)
    except telegram.error.BadRequest as e:
        await context.bot.send_photo(chat_id, img['url'], caption=''.join(text.split()[:50]), reply_markup=markup)


def parser_film(response):
    alt_name = response['alternativeName']
    name = response['name']
    description = response['description']
    # years = '-'.join([response['releaseYears'][0]['start'], response['releaseYears'][0]['end']])
    age_rate = response['ageRating']
    genre = ', '.join(map(lambda x: x['name'], response['genres'][:5]))
    poster = response['poster']
    rate_imdb, rate_kp = response['rating']['imdb'], response['rating']['kp']
    persons = response['persons'][:5] if len(response['persons']) >= 5 else response['persons'][
                                                                            :len(response['persons'])]
    persons = [x['name'] if x['name'] is not None else x['enName'] for x in persons]
    persons = ', '.join(persons)
    text = f"""{name} {f'({alt_name})' if alt_name is not None else ''} {str(age_rate) + '+' if age_rate else ''}
                жанр: {genre}
                IMDb: {rate_imdb}, Кинопоиск: {rate_kp}
                актёры: {persons}\n
                {description}
                """
    return text, poster


async def search_by_name(query, context):
    keyboard = [[InlineKeyboardButton('Назад', callback_data='search')]]
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('Напишите название фильма', reply_markup=markup)
