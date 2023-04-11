import logging
from pprint import pprint

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import API_KEY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    context.params = {'chat_id': update.message.chat_id}
    keyboard = [[InlineKeyboardButton("Поиск фильма", callback_data='search'),
                 InlineKeyboardButton("Оценки фильмов", callback_data='assessments')],
                [InlineKeyboardButton("Мои фильмы", callback_data='my_movies'),
                 InlineKeyboardButton("Подборки", callback_data='mixes')],
                [InlineKeyboardButton("Рандом", callback_data='random')]
                ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("HELLO", reply_markup=reply_markup)


async def button(update, context):
    chat_id = context.params['chat_id']
    query = update.callback_query
    await query.answer()
    dt = query.data
    if dt == 'random':
        await random(query, context, chat_id)
        return 0
    await query.edit_message_text(f"Вы нажали {query.data}")


async def get_response(url, params={}, headers={}):
    logger.info(f"getting {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            return await resp.json()


async def random(query, context, chat_id):
    uri = 'https://api.kinopoisk.dev/v1/movie/random'
    response = await get_response(uri, headers={'X-API-KEY': API_KEY})
    pprint(response)
    text, img = parser_film(response)
    await context.bot.send_photo(chat_id, img, caption=text)



def parser_film(response):
    alt_name = response['alternativeName']
    name = response['name']
    description = response['description']
    # years = '-'.join([response['releaseYears'][0]['start'], response['releaseYears'][0]['end']])
    age_rate = response['ageRating']
    genre = ', '.join(map(lambda x: x['name'], response['genres'][:5]))
    poster = response['poster']
    rate_imdb, rate_kp = response['rating']['imdb'], response['rating']['kp']
    persons = response['persons'][:5] if len(response['persons']) >= 5 else response['persons'][:len(response['persons'])]
    persons = [x['name'] if x['name'] is not None else x['enName'] for x in persons]
    persons = ', '.join(persons)
    text = f"""{name} {f'({alt_name})' if alt_name is not None else ''} {str(age_rate) + '+' if age_rate else ''}
                жанр: {genre}
                IMDb: {rate_imdb}, Кинопоиск: {rate_kp}
                актёры: {persons}\n
                описание: {description}
                """
    return text, poster
