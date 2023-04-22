import sqlite3


def add_to_want_films(chat_id, name_film, id_film):
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        result = cur.execute(f'select * from user where chat_id = {int(chat_id)}').fetchall()
    if result[0][3]:
        films = result[0][3].split(',')
        if str(id_film) not in films:
            films.append(str(id_film))
            films = ','.join(films)
            params = (films,)
            cur.execute(f'update user set want_films = ? where chat_id = {int(chat_id)}', params)
            db_file.commit()
            return 'add_to_want'
        else:
            index1 = films.index(str(id_film))
            del films[index1]
            params = (','.join(films),)
            cur.execute(f'update user set want_films = ? where chat_id = {int(chat_id)}', params)
            db_file.commit()
            return 'delete_from_want'
    else:
        params = (id_film,)
        cur.execute(f'update user set want_films = ? where chat_id = {int(chat_id)}', params)
        db_file.commit()
        return 'add_to_want'


def add_film_title_to_db(id, title):
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        result = cur.execute(f'select * from films where id = {id}').fetchall()
    if result:
        return 'already_exist'
    else:
        params = (id, title)
        cur.execute(f'insert into films(id, title) values (?, ?)', params)
        db_file.commit()
        return 'add_film'


def register_user(chat_id, name):
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        result = cur.execute(f'select * from user where chat_id = {int(chat_id)}').fetchall()
    if result:
        return 'already_registered'
    else:
        params = (chat_id, name)
        cur.execute(f'insert into user(chat_id, name) values (?, ?)', params)
        db_file.commit()
        return 'registered'


def get_all_later(id):
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        result = cur.execute(f'select want_films from user where chat_id = {id}').fetchall()
        return result


def get_all_watched(id):
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        result = cur.execute(f'select watch_films from user where chat_id = {int(id)}').fetchall()
        return result


def get_all_from_films():
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        result = cur.execute(f'select * from films').fetchall()
        return result


def add_to_watched(id, name, id_film):
    flag = False
    if get_all_later(int(id))[0][0]:
        if str(id_film) in get_all_later(id)[0][0].split(','):
            later_films = get_all_later(id)[0][0].split(',')
            index_1 = later_films.index(str(id_film))
            del later_films[index_1]
            later_films = ','.join(later_films)
            flag = True
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        params = (id,)
        result = cur.execute('select watch_films from user where chat_id = ?', params).fetchall()
    if result[0][0]:
        films = result[0][0].split(',')
        if str(id_film) not in films:
            films.append(str(id_film))
        else:
            if not flag:
                index1 = films.index(str(id_film))
                del films[index1]
        films = ','.join(films)
    else:
        films = f'{id_film}'
    if flag:
        params = (later_films,)
        cur.execute(f'update user set want_films = ? where chat_id = {int(id)}', params)
    params = (films,)
    cur.execute(f'update user set watch_films = ? where chat_id = {int(id)}', params)
    db_file.commit()
    return 'add_to_watched'


def get_all_films_from_id(id):
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        result = cur.execute(f'select want_films, watch_films from user where chat_id = {int(id)}').fetchall()
        films = ''
        if result:
            if result[0][0]:
                films = result[0][0]
            if result[0][1]:
                if films:
                    films += f',{result[0][1]}'
                else:
                    films = result[0][1]
            return films.split(',')
        else:
            return ''


if __name__ == '__main__':
    print(get_all_films_from_id(1))
