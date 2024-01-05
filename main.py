import asyncio
import logging
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, CommandObject
from aiogram.methods import SendMessage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.utils.formatting import Text
from magic_filter import F

import config
from commands import generate_score, add_admin, add_user, edit_timer, edit_score_start, edit_score_end, delete_admin, \
    get_active_admins, get_statistics_admin
from connection_mongo import database
from config import MONGODB_URL, TELEGRAM_BOT_TOKEN
from UserRepo import UserRepo, User

bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

FindScoreCommand = CommandObject(command="/find_score")
AddUserCommand = CommandObject(command="/add_user")
AddAdminCommand = CommandObject(command="/add_admin")
EditTimerCommand = CommandObject(command="/edit_timer")
EditScoreStartCommand = CommandObject(command="/edit_score_start")
EditScoreEndCommand = CommandObject(command="/edit_score_end")
DeleteAdminCommand = CommandObject(command="/delete_admin")


async def get_keyboard(role: str):
    match role:
        case 'owner':
            keyboard = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text='Активные администраторы'),  KeyboardButton(text='Изменить таймер')],
                [KeyboardButton(text='Добавить администратора'), KeyboardButton(text='Удалить администратора')],
                [KeyboardButton(text='Изменить коэффициента входа'), KeyboardButton(text='Изменить когда забирать')],
                [KeyboardButton(text='Добавить пользователя'), KeyboardButton(text='Получить следующий коэффициент')],
            ], resize_keyboard=True)
            # keyboard.add(KeyboardButton(text='Добавить пользователя'))
            # keyboard.add(KeyboardButton(text='Добавить админа'))
            # keyboard.add(KeyboardButton(text='Изменить таймер'))
            # keyboard.add(KeyboardButton(text='Изменить score_start'))
            # keyboard.add(KeyboardButton(text='Изменить score_end'))
            # keyboard.add(KeyboardButton(text='Удалить админа'))
        case 'admin':
            keyboard = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text='Добавить пользователя'), KeyboardButton(text='Получить следующий коэффициент')]],
                resize_keyboard=True)
        case _:
            keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Получить следующий коэффициент')]],
                                           resize_keyboard=True)
        # case _:
        #     keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Активировать доступ')]],
        #                                    resize_keyboard=True, request_contact=True)
        # keyboard.add(KeyboardButton(text='Запросить доступ'))
    return keyboard


@dp.message(CommandStart())
async def start_command(message):
    user = await UserRepo.find_by_name(message.from_user.username)
    if user is not None:
        user.telegram_id = message.from_user.id
        match user.role:
            case 'owner':
                answer = 'You are owner'
                await UserRepo.update(user)
                keyboard = await get_keyboard('owner')
            case 'admin':
                answer = 'You are admin'
                await UserRepo.update(user)
                keyboard = await get_keyboard('admin')
            case _:
                answer = 'Доступ оплачен, для старта нажми кнопку "Получить следующий коэффициент"'
                await UserRepo.update(user)
                keyboard = await get_keyboard('user')
    else:
        # await add_admin(message.from_user.username)
        answer = 'Обратись к администратору для получения доступа к софту'
        keyboard = await get_keyboard('')
    await bot.send_message(message.from_user.id, answer, reply_markup=keyboard)


@dp.message()
async def get_text_messages(message):
    user = await UserRepo.find_by_tg_id(message.from_user.id)
    if user is not None:
        match user.role:
            case 'owner':
                answer, mackup = await owners_command(message, user)
                if mackup is None:
                    await get_keyboard('owner')
            case 'admin':
                answer = await admins_command(message, user)
                mackup = await get_keyboard('admin')
            case _:
                answer = await users_command(message, user)
                mackup = await get_keyboard('user')
    else:
        answer = 'Обратись к администратору для получения доступа к софту'
        mackup = None
    await bot.send_message(message.from_user.id, answer, reply_markup=mackup)
    return ''


async def get_admin_stats(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = await UserRepo.find_by_tg_id(user_id)
    if user is None:
        answer = 'У вас нет доступа'
        return
    if user.role != 'owner':
        answer = 'У вас нет доступа'
        return
    admin_id = callback_query.data.split(' ')[1]
    answer = await get_statistics_admin(admin_id)
    await bot.send_message(user_id, answer)


async def owners_command(message, user: User):
    answer = 'Неизвестная команда'
    mackup = None
    if message.text == 'Получить следующий коэффициент':
        return await generate_score(user), None
    if user.processed_command is False:
        match message.text:
            case 'Добавить администратора':
                user.processed_command = True
                user.current_command = 'Добавить администратора'
                await UserRepo.update(user)
                answer = 'Введите имя администратора без собаки'
            case 'Добавить пользователя':
                user.processed_command = True
                user.current_command = 'Добавить пользователя'
                await UserRepo.update(user)
                answer = 'Введите имя пользователя без собаки'
            case 'Изменить таймер':
                user.processed_command = True
                user.current_command = 'Изменить таймер'
                await UserRepo.update(user)
                answer = 'Введите новый диапазон таймера в секундах\n Например: 300 600'
            case 'Изменить коэффициента входа':
                user.processed_command = True
                user.current_command = 'Изменить коэффициента входа'
                await UserRepo.update(user)
                answer = 'Введите новый диапазон коэффициента входа\n Например: 1.5 3'
            case 'Изменить когда забирать':
                user.processed_command = True
                user.current_command = 'Изменить когда забирать'
                await UserRepo.update(user)
                answer = 'Введите новый диапазон когда забирать\n Например: 1.5 3'
            case 'Удалить администратора':
                user.processed_command = True
                user.current_command = 'Удалить админа'
                await UserRepo.update(user)
                answer = 'Введите имя администратора без собаки'
            case 'Активные администраторы':
                answer, mackup = await get_active_admins(user.id)
    else:
        text = message.text.split(' ')
        match user.current_command:
            case 'Добавить администратора':
                answer = await add_admin(text[0], user.id)
            case 'Добавить пользователя':
                answer = await add_user(text[0], user.id)
            case 'Изменить таймер':
                answer = await edit_timer(text[0], text[1])
            case 'Изменить коэффициента входа':
                answer = await edit_score_start(text[0], text[1])
            case 'Изменить когда забирать':
                answer = await edit_score_end(text[0], text[1])
            case 'Удалить админа':
                answer = await delete_admin(text[0])
        user.current_command = ''
        user.processed_command = False
        await UserRepo.update(user)
    return answer, mackup


async def admins_command(message, user: User):
    answer = 'Неизвестная команда'
    if message.text == 'Получить следующий коэффициент':
        return await generate_score(user)
    if user.processed_command is False:
        if message.text == 'Добавить пользователя':
            user.processed_command = True
            user.current_command = 'Добавить пользователя'
            await UserRepo.update(user)
            answer = 'Введите имя пользователя без собаки'
    else:
        text = message.text.split(' ')
        if user.current_command == 'Добавить администратора':
            answer = await add_user(text[0], user.id)
        user.current_command = ''
        user.processed_command = False
        await UserRepo.update(user)
    return answer


async def users_command(message, user: User):
    if message.text == 'Получить следующий коэффициент':
        return await generate_score(user)
    return 'Неизвестная команда'


# # Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     start_up()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
async def load_data():
    with open('timer.txt', 'r') as file:
        row = file.read().split(' ')
        config.timer_frt, config.timer_second = float(row[0]), float(row[1])
    with open('score_start.txt', 'r') as file:
        row = file.read().split(' ')
        config.score_start_frt, config.score_start_second = float(row[0]), float(row[1])
    with open('score_end.txt', 'r') as file:
        row = file.read().split(' ')
        config.score_end_frt, config.score_end_second = float(row[0]), float(row[1])


async def main() -> None:
    # TODO: add load score on start up
    await load_data()
    dp.callback_query.register(get_admin_stats, F.data.startswith('admin'))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
