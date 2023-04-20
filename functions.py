import asyncio
import logging
from pprint import pprint

import aiohttp
from aiogram import types
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import API_KEY, API_KEY_2
from db_functions import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    if 'chat_id' not in context.user_data:
        context.user_data['chat_id'] = update.message.chat_id
        context.user_data['username'] = update.message.from_user.username
        context.user_data['id'] = update.message.from_user.id
        print(register_user(context.user_data['id'], context.user_data['username']))
    keyboard = [[InlineKeyboardButton("Поиск фильма", callback_data='search'),
                 InlineKeyboardButton("Мой кабинет", callback_data='my_cabinet')],
                [InlineKeyboardButton("Мои фильмы", callback_data='my_movies'),
                 InlineKeyboardButton("Подборки", callback_data='mixes')],
                [InlineKeyboardButton("Рандом", callback_data='random')]
                ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if 'message_type' not in context.user_data: context.user_data['message_type'] = ' '
    print(context.user_data['message_type'])
    if context.user_data['message_type'] != 'text':
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(text=
                                                                      "Добро пожаловать в стартовое меню бота.\nЗдесь вы можете найти нужную вам функцию.",
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=reply_markup)
    else:
        print(123, context.user_data['message_type'])
        context.user_data['message'] = await context.bot.edit_message_text(text=
                                                                           "Добро пожаловать в стартовое меню бота.\nЗдесь вы можете найти нужную вам функцию.",
                                                                           message_id=context.user_data[
                                                                               'message'].message_id,
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
        if query.data.startswith('search_by_name'):
            await random(context, 'https://api.kinopoisk.dev/v1/movie', params={'name': query.data.split('~')[1]},
                         dlt=True)
        if query.data == 'search_by_actor':
            await search_by_person(query, context, key=1)
        if query.data == 'search_by_director':
            await search_by_person(query, context, key=2)
        if query.data == 'search_by_genre':
            await search_by_genre(context)
        if query.data.startswith('search_by_id'):
            await random(context, 'https://api.kinopoisk.dev/v1/movie', params={'id': query.data.split('.')[1]},
                         dlt=True)
        if query.data == 'random':
            await random(context, 'https://api.kinopoisk.dev/v1/movie/random')
        if query.data == 'start':
            await start(update, context)
        if query.data.split('.')[0] == 'add_to_watched':
            print(add_to_watched(context.user_data['id'], context.user_data['username'], int(query.data.split('.')[1])))
        if query.data == 'my_cabinet':
            await cabinet(query, context)
        if query.data.split('.')[0] == 'watch_later':
            await watch_later(query, context)
        if query.data.split('.')[0] == 'print_films_by_person':
            await print_films_by_person(context, query.data, None)
        if query.data == 'delete':
            await context.bot.delete_message(chat_id=context.user_data['chat_id'],
                                             message_id=context.user_data['message'].message_id)
            context.user_data['message_type'] = 'text_media'
        if query.data == 'list_of_genres':
            await list_of_genres(context)
        if query.data.split('.')[0] == 'add_to_want_films':
            print(add_to_want_films(context.user_data['id'], context.user_data['username'], query.data.split('.')[1]))

    else:
        if 'query_data' in context.user_data:
            name = update.message.text
            if context.user_data['query_data'] == 'search_by_name':
                print(context.user_data)
                await random(context, 'https://api.kinopoisk.dev/v1/movie', params={'name': name})
            if context.user_data['query_data'] == 'search_by_actor':
                print(context.user_data)
                await print_films_by_person(context, 'print_films_by_person',
                                            'https://kinopoiskapiunofficial.tech/api/v1/persons',
                                            params={'name': name},
                                            headers={"X-API-KEY": API_KEY_2}, key=1)
            if context.user_data['query_data'] == 'search_by_director':
                print(context.user_data)
                await print_films_by_person(context, 'print_films_by_person',
                                            'https://kinopoiskapiunofficial.tech/api/v1/persons',
                                            params={'name': name},
                                            headers={"X-API-KEY": API_KEY_2}, key=2)
            if context.user_data['query_data'] == 'search_by_genre':
                await print_film_by_genre(context, params={'genres.name': name.lower()},
                                          headers={"X-API-KEY": API_KEY})
            del context.user_data['query_data']


async def watch_later(query, context):
    query_data = query.data.split('.')
    if query_data[1] == '0':
        later_data = get_all_later(context.user_data['id'])
        text = 'Список фильмов и сериалов, которые вы хотите посмотреть позже.'
    else:
        later_data = get_all_watched(context.user_data['id'])
        text = 'Список фильмов и сериалов, которые вы посмотрели.'
    keyboard = []
    if later_data[0][0]:
        if len(query_data) == 2:
            all_watch = get_all_from_films()
            context.user_data['dict_films'] = {}
            for i in all_watch:
                context.user_data['dict_films'][i[0]] = i[1]
            later_data = later_data[0]
            c = 1
            context.user_data['dict_of_later_watch'] = {}
            for i in range(0, len(later_data[0].split(',')), 8):
                context.user_data['dict_of_later_watch'][c] = later_data[0].split(',')[i:i + 8]
                c += 1
            query_data.append(1)
        markup_data = context.user_data['dict_of_later_watch'][int(query_data[-1])]
        print(markup_data)
        print(context.user_data['dict_of_later_watch'])
        for i in range(0, len(markup_data), 2):
            keyboard.append(
                [InlineKeyboardButton(context.user_data["dict_films"][int(i)], callback_data=f'search_by_id.{i}') for i
                 in
                 markup_data[i:i + 2]])
        next_previous = []
        if int(query_data[-1]) != 1:
            next_previous.append(
                InlineKeyboardButton('<', callback_data=f'watch_later.{query_data[1]}.{int(query_data[-1]) - 1}'))
        if int(query_data[-1]) != len(context.user_data['dict_of_later_watch']):
            next_previous.append(
                InlineKeyboardButton('>', callback_data=f'watch_later.{query_data[1]}.{int(query_data[-1]) + 1}'))
        if next_previous:
            keyboard.append(next_previous)
    keyboard.append([InlineKeyboardButton('Назад', callback_data='my_cabinet')])
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text':
        context.user_data['message'] = await context.bot.edit_message_text(
            text=text,
            chat_id=context.user_data['chat_id'],
            reply_markup=markup,
            message_id=context.user_data[
                'message'].message_id)
    else:
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(
            text=text,
            chat_id=context.user_data['chat_id'],
            reply_markup=markup)


async def cabinet(query, context):
    keyboard = [
        [InlineKeyboardButton('Посмотреть позже', callback_data='watch_later.0'),
         InlineKeyboardButton('Уже смотрел', callback_data='watch_later.1')],
        [InlineKeyboardButton('Назад', callback_data='start')]]
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text':
        context.user_data['message'] = await context.bot.edit_message_text(
            text=f'Кабинет @{context.user_data["username"]}',
            chat_id=context.user_data['chat_id'],
            reply_markup=markup,
            message_id=context.user_data[
                'message'].message_id)
    else:
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(text=f'Кабинет @{context.user_data["username"]}',
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=markup)


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
            return await resp.json(), str(resp.ok)


async def check_ok(context, ok):
    if not ok:
        keyboard = [[InlineKeyboardButton('Домой', callback_data='start')]]
        markup = InlineKeyboardMarkup(keyboard)
        context.user_data['message'] = await context.bot.send_message(
            text='Похоже что-то пошло не так!\nВы будете перенаправлены на домашнюю страницу',
            chat_id=context.user_data['chat_id'], reply_markup=markup)
    else:
        return 1


async def random(context, url, params=None, dlt=False):
    response, ok = await get_response(url, headers={'X-API-KEY': API_KEY}, params=params)
    text, img, url_trailer, url_sources, id_film, title = parser_film(response)
    print(add_film_title_to_db(id_film, title))
    chat_id = context.user_data['chat_id']
    special_data = 'delete' if dlt else 'start'
    if url == 'https://api.kinopoisk.dev/v1/movie/random':
        keyboard = [[InlineKeyboardButton('Рандом', callback_data='random')],
                    [InlineKeyboardButton('Назад', callback_data=special_data)]]
    else:
        keyboard = [[InlineKeyboardButton('Другое название', callback_data='search_by_name')],
                    [InlineKeyboardButton('Назад', callback_data=special_data)]]

    keyboard[0] = [InlineKeyboardButton('Трейлер', url=url_trailer)] + keyboard[0] if url_trailer else keyboard[0]
    keyboard.insert(1, [InlineKeyboardButton('Посмотреть позже', callback_data=f'add_to_want_films.{id_film}'),
                        InlineKeyboardButton('Уже смотрел', callback_data=f'add_to_watched.{id_film}')])
    keyboard = [[InlineKeyboardButton(text=k, url=v) for k, v in
                 url_sources.items()]] + keyboard if url_sources else keyboard
    print(keyboard)
    markup = InlineKeyboardMarkup(keyboard)
    print(context.user_data['message_type'])
    if context.user_data['message_type'] != 'media':
        context.user_data['message'] = await context.bot.send_photo(chat_id, img['url'], caption=text,
                                                                    reply_markup=markup,
                                                                    parse_mode=types.ParseMode.HTML)
        context.user_data['message_type'] = 'media'
    else:
        await context.bot.delete_message(chat_id, context.user_data['message'].message_id)
        context.user_data['message'] = await context.bot.send_photo(chat_id, img['url'], caption=text,
                                                                    reply_markup=markup,
                                                                    parse_mode=types.ParseMode.HTML)


def parser_film(response):
    pprint(response)
    response = response['docs'][0] if 'docs' in response else response
    id_film = response['id']
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
    pprint(persons)
    if rate_imdb and rate_imdb > 7:
        if persons:
            for k, v in persons.items():
                if len(v): persons_text += f"<strong>{k}</strong>: {', '.join(v)}\n"
    else:
        if persons:
            if persons['Режиссеры']: persons_text += f"<strong>Режиссёры</strong>: {', '.join(persons['Режиссеры'])}\n"
            if persons['Актеры']: persons_text += f"<strong>Актёры</strong>: {', '.join(persons['Актеры'])}\n"

    text = f"<strong>{year if year else ''}</strong>\n<strong>{name}</strong> {f'(<strong>{alt_name}</strong>)' if alt_name is not None else ''} <strong>{str(age_rate) + '+' if age_rate else ''}</strong>\n" \
           f"<strong>жанр:</strong> {genre}\n" \
           f"<strong>IMDb:</strong> {rate_imdb if rate_imdb else '-'}\n<strong>Кинопоиск</strong>: {rate_kp}\n" \
           f"{persons_text}\n" \
           f"{description if description else ''}"
    while len(text) > 4096: text = '\n'.join(text.split('\n')[:-1])
    return text, poster, url_trailer, sources, id_film, name


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


async def search_by_person(query, context, key=1):
    keys = {1: 'актёра', 2: 'режиссёра'}
    keyboard = [[InlineKeyboardButton('Назад', callback_data='search')]]
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text':
        context.user_data['message'] = await context.bot.edit_message_text(text=f'Напишите имя {keys[key]}',
                                                                           chat_id=context.user_data['chat_id'],
                                                                           reply_markup=markup,
                                                                           message_id=context.user_data[
                                                                               'message'].message_id)
    else:
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(text=f'Напишите имя {keys[key]}',
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=markup)


async def print_films_by_person(context, query_data, url, params=None, headers=None, key=1):
    query_data1 = query_data.split('.')
    keys = {1: ['актёр', 'ACTOR'], 2: ['режиссёр', 'DIRECTOR']}
    if len(query_data1) == 1:
        response = await get_response(url, headers={'X-API-KEY': API_KEY_2}, params=params)
        pprint(response)
        id = response['items'][0]['kinopoiskId']
        img = response['items'][0]['posterUrl']
        context.user_data['photo'] = img
        context.user_data['name'] = response['items'][0]['nameRu']
        response = await get_response('https://kinopoiskapiunofficial.tech/api/v1/staff/' + str(id), headers=headers)
        names = []
        for item in response['films']:
            if item['professionKey'] == keys[key][1]:
                if item['rating']:
                    names.append((item['nameRu'], float(item['rating'])))
        names.sort(key=lambda x: -x[1])
        pprint(names)
        names = list(map(lambda x: x[0], names))
        context.user_data['films_by_enter'] = {}
        c = 1
        for i in range(0, len(names), 8):
            context.user_data['films_by_enter'][c] = names[i:i + 8]
            c += 1
        query_data1.append(1)
    print(context.user_data['films_by_enter'])
    keyboard = []
    markup_data = context.user_data['films_by_enter'][int(query_data1[-1])]
    for i in range(0, len(markup_data), 2):
        keyboard.append([InlineKeyboardButton(name[:21], callback_data=f'search_by_name~{name[:20]}') for name in
                         markup_data[i:i + 2]])
    next_previous = []
    if int(query_data1[-1]) != 1:
        next_previous.append(
            InlineKeyboardButton('<', callback_data=f'print_films_by_person.{int(query_data1[-1]) - 1}'))
    if int(query_data1[-1]) != len(context.user_data['films_by_enter']):
        next_previous.append(
            InlineKeyboardButton('>', callback_data=f'print_films_by_person.{int(query_data1[-1]) + 1}'))
    if next_previous:
        keyboard.append(next_previous)
    keyboard.append([InlineKeyboardButton(f'Другой {keys[key][0]}', callback_data=f'search_by_{keys[key][1].lower()}'),
                     InlineKeyboardButton('Назад', callback_data='search')])
    markup = InlineKeyboardMarkup(keyboard)
    pprint(markup)
    if context.user_data['message_type'] == 'text_media':
        context.user_data['message'] = await context.bot.delete_message(chat_id=context.user_data['chat_id'],
                                                                        message_id=context.user_data[
                                                                            'message'].message_id)
    context.user_data['message_type'] = 'text_media'
    context.user_data['message'] = await context.bot.send_photo(context.user_data['chat_id'],
                                                                context.user_data['photo'],
                                                                caption=context.user_data['name'],
                                                                reply_markup=markup,
                                                                parse_mode=types.ParseMode.HTML)


async def search_by_genre(context):
    keyboard = [[InlineKeyboardButton('Открыть список жанров', callback_data='list_of_genres')],
                [InlineKeyboardButton('Назад', callback_data='search')]]
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text':
        context.user_data['message'] = await context.bot.edit_message_text(text='Напишите название жанра',
                                                                           chat_id=context.user_data['chat_id'],
                                                                           reply_markup=markup,
                                                                           message_id=context.user_data[
                                                                               'message'].message_id)
    else:
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(text='Напишите название жанра',
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=markup)


async def print_film_by_genre(context, params=None, headers=None):
    genres = ['аниме', 'биография', 'боевик', 'вестерн', 'военный', 'детектив', 'детский', 'для взрослых',
              'документальный', 'драма', 'игра', 'история', 'комедия', 'концерт', 'короткометражка', 'криминал',
              'мелодрама', 'музыка', 'мультфильм', 'мюзикл', 'новости', 'приключения', 'реальное ТВ', 'семейный',
              'спорт', 'ток-шоу', 'триллер', 'ужасы', 'фантастика', 'фильм-нуар', 'фэнтези', 'церемония']
    genre = params['genres.name']
    if genre not in genres:
        context.user_data['message'] = await context.bot.send_message(
            text='Что-то пошло не так\nИли вы ошиблись в названии\nПопробуйте ещё раз',
            chat_id=context.user_data['chat_id'])
        await asyncio.sleep(1)
        await search_by_genre(context)
    else:
        await random(context, 'https://api.kinopoisk.dev/v1/movie', params=params)


async def list_of_genres(context):
    genres = ['аниме', 'биография', 'боевик', 'вестерн', 'военный', 'детектив', 'детский', 'для взрослых',
              'документальный', 'драма', 'игра', 'история', 'комедия', 'концерт', 'короткометражка', 'криминал',
              'мелодрама', 'музыка', 'мультфильм', 'мюзикл', 'новости', 'приключения', 'реальное ТВ', 'семейный',
              'спорт', 'ток-шоу', 'триллер', 'ужасы', 'фантастика', 'фильм-нуар', 'фэнтези', 'церемония']
    # нужно сделать листание жанров!!!
