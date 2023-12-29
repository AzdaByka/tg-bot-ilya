import random
from datetime import datetime, timezone, timedelta

import config
from config import score_start_frt, score_start_second, score_end_frt, score_end_second, timer_frt, timer_second

from UserRepo import User, UserRepo

score_template = """
🔔СИГНАЛ!🔔

📈Время входа на линию: ПОСЛЕ КОЭФФИЦИЕНТА more score_start

💸 Забираем выигрыш на
коэффициенте score_end

Следующий сигнал в data по мск
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
    now = now + timedelta(seconds=timer_seconds)
    await UserRepo.update_query(user.id, {"date_next_call": now})
    answer = score_template.replace("more", more) \
        .replace("score_start", str(score_start)) \
        .replace("score_end", str(score_end)).replace("data", now.strftime("%H:%M:%S"))
    return answer


async def add_admin(user_name: str) -> str:
    user = await UserRepo.find_by_name(user_name)
    if user is not None:
        return 'Такой админ уже есть'
    else:
        await UserRepo.insert(User(name=user_name, role='admin', date_next_call=datetime.utcnow() + timedelta(hours=3)))
        return 'Админ добавлен'


async def add_user(user_id: int) -> str:
    user = await UserRepo.find_one(user_id)
    if user is not None:
        return 'Такой пользователь уже есть'
    else:
        await UserRepo.insert(User(id=user_id, role='user', date_next_call=datetime.utcnow() + timedelta(hours=3)))
        return 'Пользователь добавлен'


async def edit_timer(_timer_frt: str, _timer_second: str) -> str:
    config.timer_frt = _timer_frt
    config.timer_second = _timer_second
    await save_in_file('timer.txt', _timer_frt + ' ' + _timer_second)
    return 'Таймер обновлен'


async def edit_score_start(_score_start_frt: str, _score_start_second: str) -> str:
    config.score_start_frt = _score_start_frt
    config.score_start_second = _score_start_second
    await save_in_file('score_start.txt', _score_start_frt + ' ' + _score_start_second)
    return 'score_start обновлен'


async def edit_score_end(_score_end_frt: str, _score_end_second: str) -> str:
    config.score_end_frt = _score_end_frt
    config.score_end_second = _score_end_second
    await save_in_file('score_end.txt', _score_end_frt + ' ' + _score_end_second)
    return 'score_end обновлен'


async def delete_admin(user_name: str) -> str:
    user = await UserRepo.find_by_name(user_name)
    if user is None:
        return 'Такой админ не существует'
    else:
        await UserRepo.delete_one(user_name)
        return 'Админ удален'


async def save_in_file(file_name: str, text: str):
    with open(file_name, 'w') as file:
        file.write(text)
