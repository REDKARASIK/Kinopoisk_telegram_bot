import sqlite3


def add_to_want_films(chat_id, name_film, id_film):
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        result = cur.execute(f'select * from user where chat_id = {int(chat_id)}').fetchall()
    if result:
        films = result[0][3].split(',')
        if str(id_film) not in films:
            films.append(str(id_film))
            films = ','.join(films)
            params = (films,)
            cur.execute(f'update user set want_films = ? where chat_id = {int(chat_id)}', params)
            db_file.commit()
            return 'add_to_want'
        else:
            return 'already_add'
    else:
        params = (chat_id, name_film, id_film)
        cur.execute('insert into user(chat_id, name, want_films) values (?,?,?)', params)
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
        return 'registered'


def get_all_later(id):
    with sqlite3.connect('data/users_db.sqlite3') as db_file:
        cur = db_file.cursor()
        result = cur.execute(f'select want_films from user where chat_id = {id}').fetchall()
        return result


if __name__ == '__main__':
    print(add_to_want_films(12, "nor", 6))
    print(add_film_title_to_db(1, '12'))
