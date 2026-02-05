import sqlite3

db_session = sqlite3.connect("users.db")
cursor = db_session.cursor()

def get_user_info(user_id: int):
    return cursor.execute(f'SELECT name, room FROM "Users" WHERE tg_id = ?', (user_id,)).fetchone()

def add_user(user_id):
    res = cursor.execute(f'INSERT INTO "Users" (tg_id) VALUES (?)', (user_id, ))
    db_session.commit()
    return res

def update_user_name(user_id, name):
    res = cursor.execute(f'UPDATE "Users" SET name = ? WHERE tg_id = ?', (name, user_id))
    db_session.commit()
    return res

def update_user_room(user_id, room):
    res = cursor.execute(f'UPDATE "Users" SET room = ? WHERE tg_id = ?', (room, user_id))
    db_session.commit()
    return res