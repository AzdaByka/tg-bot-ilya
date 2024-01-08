import math
import random
from datetime import datetime, timezone, timedelta
from typing import List, Tuple

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
from config import score_start_frt, score_start_second, score_end_frt, score_end_second, timer_frt, timer_second

from UserRepo import User, UserRepo

score_template = """
🔔СИГНАЛ!🔔

📈Время входа на линию: ПОСЛЕ КОЭФФИЦИЕНТА more score_start

💸 Забираем выигрыш на
коэффициенте score_end

До следующего сигнала data минут
"""
tz_info = timezone(timedelta(hours=3))


async def generate_score(user: User) -> str:
    now = datetime.utcnow() + timedelta(hours=3)
    if user.date_next_call > now:
        return "Высчитываю коэффициент, ожидайте"
    more = random.choice(['БОЛЬШЕ', 'МЕНЬШЕ'])
    score_start = round(random.uniform(score_start_frt, score_start_second), 2)
    score_end = round(random.uniform(score_end_frt, score_end_second), 2)
    timer_seconds = random.randint(timer_frt, timer_second)
    minutes = math.floor(timer_seconds / 60)
    now = now + timedelta(seconds=timer_seconds)
    await UserRepo.update_query(user.id, {"date_next_call": now})
    answer = score_template.replace("more", more) \
        .replace("score_start", str(score_start)) \
        .replace("score_end", str(score_end)).replace("data", str(minutes))
    # now.strftime("%H:%M:%S"))
    return answer


async def add_admin(user_name: str, added_by: str) -> str:
    user = await UserRepo.find_by_name(user_name)
    if user is not None:
        return 'Такой админ уже есть'
    await UserRepo.insert(
        User(name=user_name, role='admin', date_next_call=datetime.utcnow() + timedelta(hours=3), added_by=added_by))
    return 'Админ добавлен'


async def add_user(username: str, added_by: str) -> str:
    user = await UserRepo.find_by_name(username)
    if user is not None:
        return 'Такой пользователь уже есть'
    await UserRepo.insert(
        User(name=username, role='user', date_next_call=datetime.utcnow() + timedelta(hours=3), added_by=added_by))
    return 'Пользователь добавлен'


async def edit_timer(_timer_frt: str, _timer_second: str) -> str:
    config.timer_frt = int(_timer_frt)
    config.timer_second = int(_timer_second)
    await save_in_file('timer.txt', _timer_frt + ' ' + _timer_second)
    return 'Таймер обновлен'


async def edit_score_start(_score_start_frt: str, _score_start_second: str) -> str:
    config.score_start_frt = float(_score_start_frt)
    config.score_start_second = float(_score_start_second)
    await save_in_file('score_start.txt', _score_start_frt + ' ' + _score_start_second)
    return 'score_start обновлен'


async def edit_score_end(_score_end_frt: str, _score_end_second: str) -> str:
    config.score_end_frt = float(_score_end_frt)
    config.score_end_second = float(_score_end_second)
    await save_in_file('score_end.txt', _score_end_frt + ' ' + _score_end_second)
    return 'score_end обновлен'


async def delete_admin(user_name: str) -> str:
    user = await UserRepo.find_by_name(user_name)
    if user is None:
        return 'Такой админ не существует'
    else:
        await UserRepo.delete_one(user_name)
        return 'Админ удален'


async def get_active_admins(owner_id: str) -> tuple[str, InlineKeyboardMarkup]:
    answer = 'Администраторы: '
    admins = await UserRepo.get_all({'role': 'admin', 'added_by': owner_id})
    buttons = []
    for admin in admins:
        buttons.append([InlineKeyboardButton(text=admin['name'], callback_data='admin ' + admin['id'])])
    buttons = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=buttons)
    return answer, buttons


async def get_statistics_admin(admin_id: str) -> str:
    _ = datetime.utcnow() - timedelta(days=9, hours=19)
    date_from = datetime(year=_.year, month=_.month, day=_.day)
    users = await UserRepo.get_all(
        {'role': 'user', 'added_by': admin_id, 'created_at': {'$gte': date_from}})
    date_list = {}
    for user in users:
        date = str(user['created_at'].day) + '.' + str(user['created_at'].month)
        if date not in date_list:
            date_list[date] = 1
        else:
            date_list[date] += 1

    answer = 'Статистика: \n'
    for date in date_list.keys():
        answer += date + '= ' + str(date_list[date]) + '\n '
    return answer


async def save_in_file(file_name: str, text: str):
    with open(file_name, 'w') as file:
        file.write(text)
