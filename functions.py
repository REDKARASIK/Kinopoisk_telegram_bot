import asyncio
import datetime
import logging
import random

import aiohttp
import telegram
import telegram.error
from aiogram import types
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import API_KEY, API_KEY_2
from db_functions import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def bot_help(update, context):
    keyboard = [[InlineKeyboardButton('🚩В главное меню', callback_data='start')]]
    markup = InlineKeyboardMarkup(keyboard)
    context.user_data['message'] = await context.bot.send_message(
        text='Благодаря нашему боту Ваше общение с киноиндустрией станет гораздо приятнее.\n'
             'Оперативный поиск фильмов и многой информации для них.\nБудем рады Вам!'
             '<strong>НАЖМИТЕ или НАПИШИТЕ /start, если что-то не работает!',
        chat_id=context.user_data['chat_id'], reply_markup=markup, parse_mode=types.ParseMode.HTML)


async def start(update, context):
    if 'chat_id' not in context.user_data:
        context.user_data['chat_id'] = update.message.chat_id
        context.user_data['username'] = update.message.from_user.username
        context.user_data['id'] = update.message.from_user.id
        print(register_user(context.user_data['id'], context.user_data['username']))
    keyboard = [[InlineKeyboardButton("🔎Поиск фильма", callback_data='search'),
                 InlineKeyboardButton("🏚Мой кабинет", callback_data='my_cabinet')],
                [InlineKeyboardButton("🎥Мои фильмы", callback_data='watch_later.1'),
                 InlineKeyboardButton("🍿Кинопремьеры", callback_data='premiers')],
                [InlineKeyboardButton("🎲Рандом", callback_data='random')]
                ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if 'message_type' not in context.user_data:
        context.user_data['message_type'] = ' '
    if context.user_data['message_type'] != 'text':
        context.user_data['message_type'] = 'text'
        text = "<strong>ГЛАВНОЕ МЕНЮ</strong>\n" \
               "Самое важное место нашего бота\n" \
               "Здесь начинается ваше погружение в МИР КИНО\n" \
               "Найди любимого актёра, проверь режиссёра,\n" \
               "Найди фильм в любимом жанре и многое другое!\n" \
               "<strong>Начинай!</strong>"
        context.user_data['message'] = await context.bot.send_message(text=text,
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=reply_markup,
                                                                      parse_mode=types.ParseMode.HTML)
    else:
        context.user_data['message'] = await context.bot.edit_message_text(text=text,
                                                                           message_id=context.user_data[
                                                                               'message'].message_id,
                                                                           chat_id=context.user_data['chat_id'],
                                                                           reply_markup=reply_markup,
                                                                           parse_mode=types.ParseMode.HTML)


async def button(update, context):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        context.user_data['query_data'] = query.data
        if query.data == 'search':
            if context.user_data['message_type'] == 'media':
                context.user_data['message'] = await context.bot.delete_message(chat_id=context.user_data['chat_id'],
                                                                                message_id=context.user_data[
                                                                                    'message'].message_id)
            await search_film(query, context)
        if query.data == 'search_by_name':
            await search_by_name(query, context)
        if query.data.startswith('psearch_by_name'):
            await universal_search_film(context, 'https://api.kinopoisk.dev/v1/movie',
                                        params={'name': query.data.split('~')[1]},
                                        dlt=True, list_of_films=False)
        if query.data == 'search_by_actor':
            await search_by_person(query, context, key=1)
        if query.data == 'search_by_director':
            await search_by_person(query, context, key=2)
        if query.data == 'search_by_genre':
            await search_by_genre(context)
        if query.data.startswith('search_by_id'):
            await universal_search_film(context, 'https://api.kinopoisk.dev/v1/movie',
                                        params={'id': query.data.split('.')[1]},
                                        dlt=True)
        if query.data == 'random':
            await universal_search_film(context, 'https://api.kinopoisk.dev/v1/movie/random')
        if query.data == 'start':
            if context.user_data['message_type'] == 'media':
                context.user_data['message'] = await context.bot.delete_message(chat_id=context.user_data['chat_id'],
                                                                                message_id=context.user_data[
                                                                                    'message'].message_id)
            await start(update, context)
        if query.data.split('.')[0] == 'add_to_watched':
            print(add_to_watched(context.user_data['id'], context.user_data['username'], int(query.data.split('.')[1])))
            await update_markup(context, context.user_data['message'].message_id, context.user_data['chat_id'],
                                int(query.data.split('.')[1]))
        if query.data == 'my_cabinet':
            await cabinet(query, context)
        if query.data == 'donation':
            await donation(query, context)
        if query.data.split('.')[0] == 'watch_later':
            await watch_later(query, context)
        if query.data.split('.')[0] == 'print_films_by_person':
            await print_films_by_person(context, query.data, None)
        if query.data.startswith('delete'):
            message_id = context.user_data['message'].message_id if len(query.data.split('.')) == 1 else \
                context.user_data['deleting_id']
            await context.bot.delete_message(chat_id=context.user_data['chat_id'],
                                             message_id=message_id)
            context.user_data['message_type'] = 'text_media'
        if query.data.split('.')[0] == 'list_of_genres':
            await list_of_genres(query.data, context)
        if query.data.split('.')[0] == 'add_to_want_films':
            print(add_to_want_films(context.user_data['id'], context.user_data['username'], query.data.split('.')[1]))
            await update_markup(context, context.user_data['message'].message_id, context.user_data['chat_id'],
                                int(query.data.split('.')[1]))
        if query.data.startswith('genre'):
            await print_film_by_genre(context, params={'genres.name': query.data.split('.')[1]},
                                      headers={"X-API-KEY": API_KEY})
        if query.data.startswith('print_by_name'):
            key = int(query.data.split('~')[1])
            await universal_search_film(context, '', my_response=context.user_data['list_of_films'][key], dlt=True)
        if query.data.startswith('print_films_by_name'):
            await print_films_by_name(context, query.data, context.user_data['list_of_films'],
                                      context.user_data['names_of_films'])
        if query.data == 'premiers':
            delta = datetime.timedelta(days=30)
            date1 = '.'.join(str(datetime.datetime.now().date()).split('-')[::-1])
            date0 = '.'.join(str((datetime.datetime.now() - delta).date()).split('-')[::-1])
            await universal_search_film(context, 'https://api.kinopoisk.dev/v1/movie',
                                        params={'premiere.russia': f'{date0}-{date1}'}, list_of_films=True)
        if query.data.startswith('awards'):
            await print_awards(context, query.data.split('.')[1])
        if query.data.startswith('review'):
            await print_review(context, query.data.split('.')[1])
        if query.data.startswith('fact'):
            await print_facts(context, query.data.split('.')[1], 'FACT')
        if query.data.startswith('blooper'):
            await print_facts(context, query.data.split('.')[1], 'BLOOPER')
    else:
        if 'query_data' in context.user_data:
            name = update.message.text
            if context.user_data['query_data'] == 'search_by_name':
                await universal_search_film(context, 'https://api.kinopoisk.dev/v1/movie', params={'name': name},
                                            list_of_films=True)
            if context.user_data['query_data'] == 'search_by_actor':
                await print_films_by_person(context, 'print_films_by_person',
                                            'https://kinopoiskapiunofficial.tech/api/v1/persons',
                                            params={'name': name},
                                            headers={"X-API-KEY": API_KEY_2}, key=1)
            if context.user_data['query_data'] == 'search_by_director':
                await print_films_by_person(context, 'print_films_by_person',
                                            'https://kinopoiskapiunofficial.tech/api/v1/persons',
                                            params={'name': name},
                                            headers={"X-API-KEY": API_KEY_2}, key=2)
            if context.user_data['query_data'] == 'search_by_genre':
                await print_film_by_genre(context, params={'genres.name': name.lower()},
                                          headers={"X-API-KEY": API_KEY})
            del context.user_data['query_data']


async def donation(query, context):
    keyboard = [[InlineKeyboardButton('🔙Назад', callback_data='my_cabinet')]]
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text':
        context.user_data['message'] = await context.bot.edit_message_text(
            text=f'Поддержать нас вы можете с помощью перевода на карту\.\n'
                 f'Номер карты \(СБЕР\): `2202206135921562`\n'
                 f'Заранее благодарим за поддержку\!',
            chat_id=context.user_data['chat_id'],
            message_id=context.user_data[
                'message'].message_id, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=markup)
    else:
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(
            text=f'Поддержать нас вы можете с помощью перевода на карту\.\n'
                 f'Номер карты \(СБЕР\): `2202206135921562`\n'
                 f'Заранее благодарим за поддержку\!',
            chat_id=context.user_data['chat_id'], parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
            reply_markup=markup)


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
        for i in range(0, len(markup_data), 2):
            keyboard.append(
                [InlineKeyboardButton(context.user_data["dict_films"][int(i)], callback_data=f'search_by_id.{i}') for i
                 in
                 markup_data[i:i + 2]])
        next_previous = []
        if int(query_data[-1]) != 1:
            next_previous.append(
                InlineKeyboardButton('👈🏻', callback_data=f'watch_later.{query_data[1]}.{int(query_data[-1]) - 1}'))
        if int(query_data[-1]) != len(context.user_data['dict_of_later_watch']):
            next_previous.append(
                InlineKeyboardButton('👉🏻', callback_data=f'watch_later.{query_data[1]}.{int(query_data[-1]) + 1}'))
        if next_previous:
            keyboard.append(next_previous)
            keyboard.append([InlineKeyboardButton('В начало', callback_data=f'watch_later.{query_data[1]}.{1}'),
                             InlineKeyboardButton('В конец',
                                                  callback_data=f'watch_later.{query_data[1]}.'
                                                                f'{len(context.user_data["dict_of_later_watch"])}')])
    keyboard.append([InlineKeyboardButton('🔙Назад', callback_data='my_cabinet')])
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
        [InlineKeyboardButton('➕Посмотреть позже', callback_data='watch_later.0'),
         InlineKeyboardButton('✔️Уже смотрел', callback_data='watch_later.1')],
        [InlineKeyboardButton('Поддержать авторов', callback_data='donation')],
        [InlineKeyboardButton('🔙Назад', callback_data='start')]]
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
    keyboard = [[InlineKeyboardButton('📝По названию', callback_data='search_by_name'),
                 InlineKeyboardButton('👨🏽‍🦱По актёру', callback_data='search_by_actor')],
                [InlineKeyboardButton('👨🏼‍🦳По режиссёру', callback_data='search_by_director'),
                 InlineKeyboardButton('🎭По жанру', callback_data='search_by_genre')],
                [InlineKeyboardButton('🔙Назад', callback_data='start')]]
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


async def check_ok(context, ok, response, url, edit=False):
    if ok == 'False' or (response.get('total', 0) == 0 and 'random' not in url and 'staff' not in url):
        user_id, name, chat_id, message_id = context.user_data['id'], context.user_data['username'], context.user_data[
            'chat_id'], context.user_data['message'].message_id
        lines = open('data/errors.txt', 'r', encoding='utf8').readlines()
        line = f"{user_id}:{name} чат:{chat_id} сообщение:{message_id}\n{response}\n\n"
        lines.append(line)
        with open('data/errors.txt', 'w', encoding='utf8') as file:
            file.writelines(lines)
        keyboard = [[InlineKeyboardButton('🏚Домой', callback_data='start')]]
        markup = InlineKeyboardMarkup(keyboard)
        if not edit:
            context.user_data['message_type'] = 'text'
            context.user_data['message'] = await context.bot.send_message(
                text='Похоже что-то пошло не так!\nВы будете перенаправлены на домашнюю страницу',
                chat_id=chat_id, reply_markup=markup)
        else:
            context.user_data['message'] = await context.bot.edit_message_text(
                text='Похоже что-то пошло не так!\nВы будете перенаправлены на домашнюю страницу',
                message_id=message_id,
                chat_id=chat_id, reply_markup=markup)
        return 0
    return 1


async def universal_search_film(context, url, params=None, dlt=False, list_of_films=False, my_response=False,
                                data='name'):
    if not my_response:
        response, ok = await get_response(url, headers={'X-API-KEY': API_KEY}, params=params)
        edit = 'random' in url
        status = await check_ok(context, ok, response, url, edit=edit)
        if not status:
            return 0
        if list_of_films:
            context.user_data['list_of_films'], context.user_data['names_of_films'] = get_data_list_of_films(response)
            context.user_data['key'] = data
            if data == 'name':
                await print_films_by_name(context, 'search_by_name', context.user_data['list_of_films'],
                                          context.user_data['names_of_films'])
            if data == 'genre':
                await print_films_by_name(context, 'search_by_genre', context.user_data['list_of_films'],
                                          context.user_data['names_of_films'])
            return 0
    else:
        response = my_response
    text, img, url_trailer, url_sources, id_film, title = parser_film(response)
    print(add_film_title_to_db(id_film, title))
    chat_id = context.user_data['chat_id']
    special_data = 'delete.1' if dlt else 'start'
    keyboard = [[InlineKeyboardButton('🏆Награды', callback_data=f'awards.{id_film}'),
                 InlineKeyboardButton('💬Отзывы', callback_data=f'review.{id_film}'),
                 InlineKeyboardButton('💥Факты', callback_data=f'fact.{id_film}'),
                 InlineKeyboardButton('❗️Ошибки', callback_data=f'blooper.{id_film}')]]
    keyboard.insert(0, [InlineKeyboardButton('🎲Рандом',
                                             callback_data='random')] if url == 'https://api.kinopoisk.dev/v1'
                                                                                '/movie/random' else [
        InlineKeyboardButton('🔄Другое название', callback_data='search_by_name')])

    keyboard[0] = [InlineKeyboardButton('🎞Трейлер', url=url_trailer)] + keyboard[0] if url_trailer else keyboard[0]
    keyboard.insert(1, get_status(id_film, chat_id))
    keyboard = [[InlineKeyboardButton(text=k, url=v) for k, v in
                 url_sources.items()]] + keyboard if url_sources else keyboard
    keyboard.append([InlineKeyboardButton('🔙Назад', callback_data=special_data)])
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] != 'media':
        context.user_data['message'] = await context.bot.send_photo(chat_id, img['url'], caption=text,
                                                                    reply_markup=markup,
                                                                    parse_mode=types.ParseMode.HTML)
        context.user_data['message_type'] = 'media'
        context.user_data['deleting_id'] = context.user_data['message'].message_id
    else:
        await context.bot.delete_message(chat_id, context.user_data['message'].message_id)
        context.user_data['message'] = await context.bot.send_photo(chat_id, img['url'], caption=text,
                                                                    reply_markup=markup,
                                                                    parse_mode=types.ParseMode.HTML)
        context.user_data['deleting_id'] = context.user_data['message'].message_id


def parser_film(response):
    response = response['docs'][0] if 'docs' in response else response
    id_film = response['id']
    alt_name = response.get('alternativeName', '')
    name = response.get('name', '')
    description = response.get('description', '')
    short_description = response.get('shortDescription', '')
    year = response.get('year', '')
    age_rate = response.get('ageRating', '')
    genre = ', '.join(map(lambda x: x['name'], response.get('genres', '')[:5]))
    poster = response.get('poster', '')
    rate_imdb, rate_kp = response['rating']['imdb'], response['rating']['kp']
    video = response.get('videos', '')
    trailer = video.get('trailers', '') if video else ''
    url_trailer = trailer[0].get('url', '') if trailer else ''
    lengthFilm = response.get('movieLength', 0)
    lengthFilm = 0 if lengthFilm is None else lengthFilm
    h, m = int(lengthFilm) // 60, int(lengthFilm) % 60
    watchability = response['watchability']['items']
    sources = {}
    if watchability:
        for source in watchability:
            sources[source['name']] = source['url']
    persons = parser_person(response.get('persons', ''))
    persons_text = ''
    if rate_imdb and rate_imdb > 7:
        if persons:
            for k, v in persons.items():
                if len(v): persons_text += f"<strong>{k}</strong>: {', '.join(v)}\n"
    else:
        if persons:
            if persons['Режиссеры']:
                persons_text += f"<strong>Режиссёры</strong>: {', '.join(persons['Режиссеры'])}\n"
            if persons['Актеры']:
                persons_text += f"<strong>Актёры</strong>: {', '.join(persons['Актеры'])}\n"
    text = f"<strong>{year if year else ''}</strong>" \
           f"\n<strong>{name}</strong>" \
           f"{str(h).rjust(2, '0')}:{str(m).rjust(2, '0')}</strong>\n" \
           f" {f'(<strong>{alt_name}</strong>)' if alt_name is not None else ''} " \
           f"<strong>{str(age_rate) + '+' if age_rate else ''}</strong><strong>\n" \
           f"<strong>жанр:</strong> {genre}\n" \
           f"<strong>IMDb:</strong> {rate_imdb if rate_imdb else '-'}\n" \
           f"<strong>Кинопоиск</strong>: {rate_kp}\n" \
           f"{persons_text}\n"
    text += description if len(text + description) <= 1024 else short_description if (
            short_description and len(text + short_description) <= 1024) else ''
    while len(text) > 1024:
        text = '\n'.join(text.split('\n')[:-1])
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
    keyboard = [[InlineKeyboardButton('🔙Назад', callback_data='search')]]
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
    keyboard = [[InlineKeyboardButton('🔙Назад', callback_data='search')]]
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
        response, ok = await get_response(url, headers={'X-API-KEY': API_KEY_2}, params=params)
        status = await check_ok(context, ok, response, url)
        if not status:
            return 0
        id = response['items'][0]['kinopoiskId']
        img = response['items'][0]['posterUrl']
        context.user_data['photo'] = img
        context.user_data['name'] = response['items'][0]['nameRu']
        url = 'https://kinopoiskapiunofficial.tech/api/v1/staff/' + str(id)
        response, ok = await get_response(url, headers=headers)
        status = await check_ok(context, ok, response, url)
        if not status:
            return 0
        names = []
        for item in response['films']:
            if item['professionKey'] == keys[key][1]:
                if item['rating'] and item['nameRu']:
                    names.append((item['nameRu'], float(item['rating'])))
        names.sort(key=lambda x: -x[1])
        names = list(map(lambda x: x[0], names))
        context.user_data['films_by_enter'] = {}
        c = 1
        for i in range(0, len(names), 8):
            context.user_data['films_by_enter'][c] = names[i:i + 8]
            c += 1
        query_data1.append(1)
    keyboard = []
    markup_data = context.user_data['films_by_enter'][int(query_data1[-1])]
    for i in range(0, len(markup_data), 2):
        keyboard.append([InlineKeyboardButton(name[:21], callback_data=f'psearch_by_name~{name[:20]}') for name in
                         markup_data[i:i + 2]])
    next_previous = []
    if int(query_data1[-1]) != 1:
        next_previous.append(
            InlineKeyboardButton('👈🏻', callback_data=f'print_films_by_person.{int(query_data1[-1]) - 1}'))
    if int(query_data1[-1]) != len(context.user_data['films_by_enter']):
        next_previous.append(
            InlineKeyboardButton('👉🏻', callback_data=f'print_films_by_person.{int(query_data1[-1]) + 1}'))
    if next_previous:
        keyboard.append(next_previous)
        keyboard.append([InlineKeyboardButton('В начало', callback_data=f'print_films_by_person.{1}'),
                         InlineKeyboardButton('В конец',
                                              callback_data=f'print_films_by_person.'
                                                            f'{len(context.user_data["films_by_enter"])}')])
    keyboard.append([InlineKeyboardButton(f'🔄Другой {keys[key][0]}',
                                          callback_data=f'search_by_{keys[key][1].lower()}'),
                     InlineKeyboardButton('🔙Назад', callback_data='search')])
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text_media':
        context.user_data['message'] = await context.bot.edit_message_reply_markup(chat_id=context.user_data['chat_id'],
                                                                                   message_id=context.user_data[
                                                                                       'message'].message_id,
                                                                                   reply_markup=markup)
    else:
        context.user_data['message_type'] = 'text_media'
        context.user_data['message'] = await context.bot.send_photo(context.user_data['chat_id'],
                                                                    context.user_data['photo'],
                                                                    caption=f'<strong>{context.user_data["name"]}'
                                                                            f'</strong>',
                                                                    reply_markup=markup,
                                                                    parse_mode=types.ParseMode.HTML)


async def search_by_genre(context):
    keyboard = [[InlineKeyboardButton('📂Открыть список жанров', callback_data='list_of_genres')],
                [InlineKeyboardButton('🔙Назад', callback_data='search')]]
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
        params['limit'] = 32
        await universal_search_film(context, 'https://api.kinopoisk.dev/v1/movie', params=params, list_of_films=True,
                                    data='genre')


async def list_of_genres(query, context):
    genres = {1: ['аниме', 'биография', 'боевик', 'вестерн', 'военный', 'детектив', 'детский', 'для взрослых'],
              2: ['документальный', 'драма', 'игра', 'история', 'комедия', 'концерт', 'короткометражка', 'криминал'],
              3: ['мелодрама', 'музыка', 'мультфильм', 'мюзикл', 'новости', 'приключения', 'реальное ТВ', 'семейный'],
              4: ['спорт', 'ток-шоу', 'триллер', 'ужасы', 'фантастика', 'фильм-нуар', 'фэнтези', 'церемония']}
    markup_query = query.split('.')
    if len(markup_query) == 1:
        markup_query.append(1)
    markup_query = int(markup_query[-1])
    keyboard = []
    for i in range(0, len(genres[markup_query]), 2):
        keyboard.append([InlineKeyboardButton(j, callback_data=f"genre.{j}") for j in genres[markup_query][i:i + 2]])
    next_previous = []
    if markup_query != 1:
        next_previous.append(InlineKeyboardButton('👈🏻', callback_data=f'list_of_genres.{markup_query - 1}'))
    if markup_query != len(genres):
        next_previous.append(InlineKeyboardButton('👉🏻', callback_data=f'list_of_genres.{markup_query + 1}'))
    if next_previous:
        keyboard.append(next_previous)
        keyboard.append([InlineKeyboardButton('В начало', callback_data=f'list_of_genres.{1}'),
                         InlineKeyboardButton('В конец',
                                              callback_data=f'list_of_genres.{len(genres)}')])
    keyboard.append([InlineKeyboardButton('Назад', callback_data='search_by_genre')])
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text':
        context.user_data['message'] = await context.bot.edit_message_text(text=f'Жанры:',
                                                                           chat_id=context.user_data['chat_id'],
                                                                           reply_markup=markup,
                                                                           message_id=context.user_data[
                                                                               'message'].message_id)
    else:
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(text=f'Жанры:',
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=markup)


def get_data_list_of_films(response):
    data = {}
    names = {}
    for line in response['docs']:
        data[line['id']] = line
        names[line['id']] = line['name'] if line['name'] else line['enName'] if line['enName'] else line[
            'alternativeName']
    return data, names


async def print_films_by_name(context, query_data, films_data, dict_names):
    key = context.user_data['key']
    keys = {'name': ['film_by_name', 'print_by_name', 'search_by_name', 'Другое название'],
            'genre': ['film_by_name', 'print_by_name', 'search_by_genre', 'Другой жанр']}
    names = list(dict_names.keys())
    query_data1 = query_data.split('.')
    if len(query_data1) == 1:
        c = 1
        context.user_data['film_by_name'] = {}
        for i in range(0, len(names), 8):
            context.user_data['film_by_name'][c] = names[i:i + 8]
            c += 1
        query_data1.append(1)
    keyboard = []
    markup_data = context.user_data['film_by_name'][int(query_data1[-1])]
    for i in range(0, len(markup_data), 2):
        keyboard.append([InlineKeyboardButton(dict_names[name][:21], callback_data=f'print_by_name~{name}') for name in
                         markup_data[i:i + 2]])
    next_previous = []
    if int(query_data1[-1]) != 1:
        next_previous.append(
            InlineKeyboardButton('👈🏻', callback_data=f'print_films_by_name.{int(query_data1[-1]) - 1}'))
    if int(query_data1[-1]) != len(context.user_data['film_by_name']):
        next_previous.append(
            InlineKeyboardButton('👉🏻', callback_data=f'print_films_by_name.{int(query_data1[-1]) + 1}'))
    if next_previous:
        keyboard.append(next_previous)
        keyboard.append([InlineKeyboardButton('В начало', callback_data=f'print_films_by_name.{1}'),
                         InlineKeyboardButton('В конец',
                                              callback_data=f'print_films_by_name.'
                                                            f'{len(context.user_data["film_by_name"])}')])
    keyboard.append([InlineKeyboardButton(f'🔄{keys[key][3]}', callback_data=keys[key][2]),
                     InlineKeyboardButton('🔙Назад', callback_data='search')])
    markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['message_type'] == 'text':
        context.user_data['message'] = await context.bot.edit_message_text(text=f'Результаты поиска:',
                                                                           chat_id=context.user_data['chat_id'],
                                                                           message_id=context.user_data[
                                                                               'message'].message_id,
                                                                           reply_markup=markup)
    else:
        context.user_data['message_type'] = 'text'
        context.user_data['message'] = await context.bot.send_message(text='Результаты поиска',
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=markup)


def get_status(film_id, chat_id):
    keyboard = [None, None]
    watched = get_all_watched(chat_id)
    watched = watched[0][0].split(',') if watched[0][0] else []
    later = get_all_later(chat_id)
    if later[0][0]:
        later = later[0][0].split(',')
    else:
        later = []
    keyboard[0] = InlineKeyboardButton('✔️Посмотреть позже',
                                       callback_data=f'add_to_want_films.{film_id}') if str(film_id) not in later \
        else InlineKeyboardButton(
        '⏳В ожидании просмотра', callback_data=f'add_to_want_films.{film_id}')
    keyboard[1] = InlineKeyboardButton('➕Уже смотрел',
                                       callback_data=f'add_to_watched.{film_id}') if str(film_id) not in watched \
        else InlineKeyboardButton(
        '✅Просмотрено', callback_data=f'add_to_watched.{film_id}')

    return keyboard


async def update_markup(context, message_id, chat_id, film_id):
    keyboard = get_status(film_id, chat_id)
    markup = context.user_data['message'].reply_markup
    inline_keyboard = list(map(lambda x: list(x), list(markup.inline_keyboard)))
    inline_keyboard[-3] = keyboard
    new_markup = InlineKeyboardMarkup(inline_keyboard)
    if markup != new_markup:
        context.user_data['message'] = await context.bot.edit_message_reply_markup(chat_id=chat_id,
                                                                                   message_id=message_id,
                                                                                   reply_markup=new_markup)


async def print_awards(context, film_id):
    response = await get_response('https://api.kinopoisk.dev/v1.1/movie/awards', headers={'X-API-KEY': API_KEY},
                                  params={'movieId': int(film_id)})
    keyboard = [[InlineKeyboardButton('🔙Назад', callback_data='delete')]]
    markup = InlineKeyboardMarkup(keyboard)
    response = response[0]
    if response['total'] == 0:
        context.user_data['message'] = await context.bot.send_message(text='Нет наград', reply_markup=markup,
                                                                      chat_id=context.user_data['chat_id'])
    else:
        awards = response['docs']
        text = ''
        for line in awards:
            who, when = line['nomination']['award']['title'], line['nomination']['award']['year']
            nomination = line['nomination']['title']
            win = 'Победа' if line['winning'] else 'Номинация'
            text += f"<strong>{who} - {when}</strong>: {nomination} <strong>({win})</strong>\n"
        context.user_data['message'] = await context.bot.send_message(text=text, reply_markup=markup,
                                                                      chat_id=context.user_data['chat_id'],
                                                                      parse_mode=types.ParseMode.HTML)


async def print_review(context, film_id):
    response = await get_response('https://api.kinopoisk.dev/v1/review', headers={'X-API-KEY': API_KEY},
                                  params={'movieId': int(film_id), 'limit': 100})
    keyboard = [[InlineKeyboardButton('🆕Ещё', callback_data=f'review.{film_id}'),
                 InlineKeyboardButton('🔙Назад', callback_data='delete')]]
    markup = InlineKeyboardMarkup(keyboard)
    response = response[0]
    if response['total'] == 0:
        context.user_data['message'] = await context.bot.send_message(text='Нет отзывов',
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=markup)
    else:
        docs = response['docs']
        reviews = []
        for data in docs:
            author = data['author'] if data['author'] else ''
            title = data['title'] if data['title'] else ''
            review = data['review'] if data['review'] else ''
            reviews.append({'author': author, 'title': title, 'review': review})
        reviews = list(filter(lambda x: len(x['author'] + x['title'] + x['review']) <= 1024, reviews))
        if reviews:
            review = random.choice(reviews)
            if context.user_data['message_type'] != 'text':
                context.user_data['message_type'] = 'text'
                context.user_data['message'] = await context.bot.send_message(
                    text=f"<strong>{review['author']}\n{review['title']}\n{review['review']}</strong>",
                    chat_id=context.user_data['chat_id'], reply_markup=markup, parse_mode=types.ParseMode.HTML)
            else:
                try:
                    context.user_data['message'] = await context.bot.edit_message_text(
                        text=f"<strong>{review['author']}\n{review['title']}\n{review['review']}</strong>",
                        message_id=context.user_data['message'].message_id,
                        chat_id=context.user_data['chat_id'], reply_markup=markup, parse_mode=types.ParseMode.HTML)
                except telegram.error.BadRequest as error:
                    context.user_data['message'] = await context.bot.edit_message_text(text='Больше нет отзывов',
                                                                                       message_id=context.user_data[
                                                                                           'message'].message_id,
                                                                                       chat_id=context.user_data[
                                                                                           'chat_id'],
                                                                                       reply_markup=markup)
        else:
            context.user_data['message'] = await context.bot.send_message(text='Нет отзывов',
                                                                          chat_id=context.user_data['chat_id'],
                                                                          reply_markup=markup)


async def print_facts(context, film_id, key):
    word = {'FACT': ['фактов', '<strong>ФАКТЫ</strong>\n'], 'BLOOPER': ['ошибок', '<strong>ОШИБКИ</strong>\n']}
    response = await get_response(f'https://kinopoiskapiunofficial.tech/api/v2.2/films/{film_id}/facts',
                                  headers={'X-API-KEY': API_KEY_2})
    response = response[0]
    keyboard = [[InlineKeyboardButton('🔙Назад', callback_data='delete')]]
    markup = InlineKeyboardMarkup(keyboard)
    if response['total'] == 0:
        context.user_data['message'] = await context.bot.send_message(text=f'Нет {word[key][0]}',
                                                                      chat_id=context.user_data['chat_id'],
                                                                      reply_markup=markup)
    else:
        text = word[key][1]
        num = 1
        for fact in response['items']:
            if not fact['spoiler'] and fact['type'] == key:
                if len(text + fact['text']) <= 1024:
                    text += f"{num}. {fact['text']}\n"
                    num += 1
                else:
                    break
        if text:
            if context.user_data['message_type'] != 'text':
                context.user_data['message_type'] = 'text'
                context.user_data['message'] = await context.bot.send_message(text=text,
                                                                              chat_id=context.user_data['chat_id'],
                                                                              reply_markup=markup,
                                                                              parse_mode=types.ParseMode.HTML)
            else:
                context.user_data['message'] = await context.bot.edit_message_text(text=text,
                                                                                   chat_id=context.user_data['chat_id'],
                                                                                   message_id=context.user_data[
                                                                                       'message'].message_id,
                                                                                   reply_markup=markup,
                                                                                   parse_mode=types.ParseMode.HTML)
        else:
            context.user_data['message'] = await context.bot.send_message(text=f'Нет {word[key][0]}',
                                                                          chat_id=context.user_data['chat_id'],
                                                                          reply_markup=markup)
