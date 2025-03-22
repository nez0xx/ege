import re
from typing import Any

from aiogram import Router
from aiogram.client import bot
from aiogram.dispatcher.filters import Command, ContentTypesFilter
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import Message, CallbackQuery

from bot.config import db, admin_description
from bot.filters import ChatType, CommandInMessage
from bot.markups import ConvertMarkdown, StandartMarkup, RemoveFromStandartMarkup

router = Router()


@router.message(Command(commands='info_admin'), ChatType(chat_type='private'))
async def admin_help(message: Message):
    await bot.SendMessage(chat_id=message.from_user.id, text=admin_description)


@router.message(Command(commands='count_subs'), ChatType(chat_type='private'))
async def count(message: Message):
    await bot.SendMessage(
        chat_id=message.from_user.id,
        text=f'👤<b><i>Количество пользователей: </i>{len(db.get_users())}</b>'
    )


@router.message(
    ContentTypesFilter(content_types="any"),
    ChatType(chat_type='private'),
    CommandInMessage(command='/notify')
)
async def spread(message: Message, text: str, photo: Any, keyboard: list):
    users = db.get_users()
    for user in users:
        try:
            if photo:
                await bot.SendPhoto(
                    chat_id=user['USER_ID'],
                    caption=text,
                    photo=photo,
                    reply_markup=ConvertMarkdown(keyboard)
                )
            else:

                await bot.SendMessage(
                    chat_id=user['USER_ID'],
                    text=text,
                    reply_markup=ConvertMarkdown(keyboard)
                )
        #except TelegramForbiddenError:
        #    db.delete_user(user['USER_ID'])
        except Exception as e:
            print(e, user)

    await bot.SendMessage(chat_id=message.from_user.id, text='✅Рассылка завершена')


@router.message(
    ContentTypesFilter(content_types="any"),
    ChatType(chat_type='private'),
    CommandInMessage(command='/new_btn')
)
async def add(message: Message, text: str, photo: Any, keyboard: list):
    title = re.findall('<b>([^<>]*)</b>', text)
    if not title:
        return
    title = title[0].strip()
    db.add_reply(title=title, description=text, photo=photo, keyboard=';'.join(keyboard))

    await bot.SendMessage(chat_id=message.chat.id, text=f'✅Кнопка {title} сохранена', reply_markup=StandartMarkup())


@router.message(Command(commands='rm_btn'), ChatType(chat_type='private'))
async def remove(message: Message):
    markup = RemoveFromStandartMarkup()
    if len(markup.inline_keyboard) == 0:
        return await bot.SendMessage(chat_id=message.chat.id, text=f'🙅‍♂️Кнопок нет')
    await bot.SendMessage(chat_id=message.chat.id, text=f'🗑️Удалить кнопку', reply_markup=markup)


@router.callback_query(
    ChatType(chat_type='private'),
    lambda call: {'data': int(call.data.split('_')[-1])} if 'remove_' in call.data else None
)
async def callback(call: CallbackQuery, data):
    title = db.get_replies()[data-1]['TITLE']
    db.delete_reply(title=title)
    await bot.DeleteMessage(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await bot.SendMessage(
        chat_id=call.message.chat.id,
        text=f'🗑️Кнопка {title} удалена',
        reply_markup=StandartMarkup()
    )
