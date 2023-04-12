import logging
from pprint import pprint

import aiohttp
from aiogram import types
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
    context.user_data['message_type'] = 'text'
    context.user_data['message'] = await context.bot.send_message(text=
                                                                  "Добро пожаловать в стартовое меню бота.\nЗдесь вы можете найти нужную вам функцию.",
                                                                  chat_id=context.user_data['chat_id'],
                                                                  reply_markup=reply_markup)



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
            await random(context, 'https://api.kinopoisk.dev/v1/movie/random')
        if query.data == 'start':
            await start(update, context)

    else:
        if 'query_data' in context.user_data:
            if context.user_data['query_data'] == 'search_by_name':
                name = update.message.text
                del context.user_data['query_data']
                print(context.user_data)
                await random(context, 'https://api.kinopoisk.dev/v1/movie', params={'name': name})


async def search_film(query, context):
    keyboard = [[InlineKeyboardButton('По названию', callback_data='search_by_name'),
                 InlineKeyboardButton('По актёру', callback_data='search_by_actor')],
                [InlineKeyboardButton('По режиссёру', callback_data='search_by_director'),
                 InlineKeyboardButton('По жанру', callback_data='search_by_genre')],
                [InlineKeyboardButton('Назад', callback_data='start')]]
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text':
        context.user_data['message'] = await context.bot.edit_message_text(
            text='Вы можете найти фильмы, по заданным вами параметрам.',
            message_id=context.user_data['message'].message_id,
            chat_id=context.user_data['chat_id'], reply_markup=markup)
    else:
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(
            text='Вы можете найти фильмы, по заданным вами параметрам.',
            chat_id=context.user_data['chat_id'], reply_markup=markup)


async def get_response(url, params=None, headers=None):
    logger.info(f"getting {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            return await resp.json()


async def random(context, url, params=None):
    response = await get_response(url, headers={'X-API-KEY': API_KEY}, params=params)
    pprint(response)
    text, img, url_trailer, url_sources = parser_film(response)
    chat_id = context.user_data['chat_id']
    print(url_sources)
    if url == 'https://api.kinopoisk.dev/v1/movie/random':
        keyboard = [[InlineKeyboardButton('Рандом', callback_data='random')],
                    [InlineKeyboardButton('Назад', callback_data='start')]]
    else:
        keyboard = [[InlineKeyboardButton('Другое название', callback_data='search_by_name'),
                     InlineKeyboardButton('Назад', callback_data='start')]]

    keyboard[0] = [InlineKeyboardButton('Трейлер', url=url_trailer)] + keyboard[0] if url_trailer else keyboard[0]
    keyboard = [[InlineKeyboardButton(text=k, url=v) for k, v in url_sources.items()],
                keyboard[0]] if url_sources else keyboard
    print(keyboard)
    markup = InlineKeyboardMarkup(keyboard)
    context.user_data['message_type'] = 'media'
    context.bot['message'] = await context.bot.send_photo(chat_id, img['url'], caption=text, reply_markup=markup,
                                                          parse_mode=types.ParseMode.HTML)


def parser_film(response):
    response = response['docs'][0] if 'docs' in response else response
    alt_name = response.get('alternativeName', '')
    name = response.get('name', '')
    description = response.get('description', '')
    year = response.get('year', '')
    age_rate = response.get('ageRating', '')
    genre = ', '.join(map(lambda x: x['name'], response.get('genres', '')[:5]))
    poster = response.get('poster', '')
    rate_imdb, rate_kp = response['rating']['imdb'], response['rating']['kp']
    video = response.get('videos', '')
    trailer = video.get('trailers', '') if video else ''
    url_trailer = trailer[0].get('url', '') if trailer else ''
    watchability = response['watchability']['items']
    sources = {}
    if watchability:
        for source in watchability:
            sources[source['name']] = source['url']
    persons = parser_person(response.get('persons', ''))
    persons_text = ''
    if rate_imdb and rate_imdb > 7:
        print(persons)
        if persons:
            for k, v in persons.items():
                if len(v): persons_text += f"<strong>{k}</strong>: {', '.join(v)}\n"
    else:
        if persons['Режиссеры']: persons_text += f"<strong>Режиссёры</strong>: {', '.join(persons['Режиссеры'])}\n"
        if persons['Актеры']: persons_text += f"<strong>Актёры</strong>: {', '.join(persons['Актеры'])}\n"

    text = f"<strong>{year if year else ''}</strong>\n<strong>{name}</strong> {f'(<strong>{alt_name}</strong>)' if alt_name is not None else ''} <strong>{str(age_rate) + '+' if age_rate else ''}</strong>\n" \
           f"<strong>жанр:</strong> {genre}\n" \
           f"<strong>IMDb:</strong> {rate_imdb if rate_imdb else '-'}\n<strong>Кинопоиск</strong>: {rate_kp}\n" \
           f"{persons_text}\n" \
           f"{description if description else ''}"
    if len(text) > 4096: text = '\n'.join(text.split('\n')[:-1]) if len(
        '\n'.join(text.split('\n')[:-1])) <= 4096 else '\n'.join(text.split('\n')[:-2])
    return text, poster, url_trailer, sources


def parser_person(response):
    if not response:
        return ''
    persons = {'Режиссеры': [], 'Продюсеры': [], 'Композиторы': [], 'Актеры': []}
    for data in response:
        if data['profession'].capitalize() in persons:
            persons[data['profession'].capitalize()].append(
                data['name'] if data['name'] is not None else data['enName'])
    persons['Актеры'] = persons['Актеры'] if len(persons['Актеры']) < 10 else persons['Актеры'][:10]
    return persons


async def search_by_name(query, context):
    keyboard = [[InlineKeyboardButton('Назад', callback_data='search')]]
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text':
        context.user_data['message'] = await context.bot.edit_message_text(text='Напишите название фильма',
                                                                           chat_id=context.user_data['chat_id'],
                                                                           reply_markup=markup,
                                                                           message_id=context.user_data[
                                                                               'message'].message_id)
    else:
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(text='Напишите название фильма',
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=markup)
