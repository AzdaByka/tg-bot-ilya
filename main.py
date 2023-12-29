import asyncio
import logging
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, CommandObject
from aiogram.methods import SendMessage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import config
from commands import generate_score, add_admin, add_user, edit_timer, edit_score_start, edit_score_end, delete_admin
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
            keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Получить следующий коэффициент')]],
                                           resize_keyboard=True)
            # keyboard.add(KeyboardButton(text='Добавить пользователя'))
            # keyboard.add(KeyboardButton(text='Добавить админа'))
            # keyboard.add(KeyboardButton(text='Изменить таймер'))
            # keyboard.add(KeyboardButton(text='Изменить score_start'))
            # keyboard.add(KeyboardButton(text='Изменить score_end'))
            # keyboard.add(KeyboardButton(text='Удалить админа'))
        case 'admin':
            keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Получить следующий коэффициент')]],
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
                answer = await owners_command(message, user)
            case 'admin':
                answer = await admins_command(message, user)
            case _:
                answer = await users_command(message, user)
    else:
        answer = 'Обратись к администратору для получения доступа к софту'
    await bot.send_message(message.from_user.id, answer)
    return ''


async def owners_command(message, user: User):
    if message.text == 'Получить следующий коэффициент':
        return await generate_score(user)
    if message.text[0] == '/':
        text = message.text.split(' ')
        command = text[0] + ' ' + text[1]
        match command:
            case '/add admin':
                return await add_admin(text[2])
            case '/add user':
                return await add_user(text[2])
            case '/edit timer':
                return await edit_timer(text[2], text[3])
            case '/edit score_start':
                return await edit_score_start(text[2], text[3])
            case '/edit score_end':
                return await edit_score_end(text[2], text[3])
            case '/delete admin':
                return await delete_admin(text[2])
    return 'Неизвестная команда'


async def admins_command(message, user: User):
    if message.text == 'Получить следующий коэффициент':
        return await generate_score(user)
    if message.text[0] == '/':
        text = message.text.split(' ')
        command = text[0] + ' ' + text[1]
        match command:
            case '/add admin':
                return await add_admin(text[2])
            case '/add user':
                return await add_user(text[2])
            case '/delete admin':
                return await delete_admin(text[2])
    return 'Неизвестная команда'


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
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
