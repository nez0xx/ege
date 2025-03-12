import asyncio
from typing import Any

from aiogram import Router, Bot
from aiogram.client import bot
from aiogram.dispatcher.filters import Command, ContentTypesFilter
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import Message

from Bot.config import db
from Bot.filters import BotIsAdmin, ChatType, CommandInMessage, FromAdmin
from Bot.markups import ConvertMarkdown

router = Router()


async def create_task(timer: dict, Bot: Bot = None):
    if timer['PHOTO']:
        if Bot:
            await Bot.send_photo(
                chat_id = timer['CHAT_ID'],
                caption = timer['TEXT'],
                photo=timer['PHOTO'],
                reply_markup=ConvertMarkdown(timer['KEYBOARD'])
            )
        else:
            await bot.SendPhoto(
                chat_id = timer['CHAT_ID'],
                caption = timer['TEXT'],
                photo=timer['PHOTO'],
                reply_markup=ConvertMarkdown(timer['KEYBOARD'])
            )
    else:
        if Bot:
            await Bot.send_message(chat_id = timer['CHAT_ID'], text = timer['TEXT'], reply_markup=ConvertMarkdown(timer['KEYBOARD']))
        else:
            await bot.SendMessage(chat_id = timer['CHAT_ID'], text = timer['TEXT'], reply_markup=ConvertMarkdown(timer['KEYBOARD']))
    await asyncio.sleep(timer['DELAY']*60)
    timer = db.get_chat_timer(timer['CHAT_ID'])
    if timer:
        await create_task(timer, Bot)


@router.message(
    Command(commands='starton'),
    ChatType(chat_type=['supergroup', 'group']),
    BotIsAdmin(),
    FromAdmin(),
    lambda msg: msg.text.replace('/starton', '').split('@')[-1].strip()
)
async def starton(message: Message):
    try:
        channel = await bot.GetChat(chat_id='@'+message.text.replace('/starton', '').split('@')[-1].strip())
        await bot.GetChatAdministrators(chat_id=channel.id)
        db.set_chat_value(
            message.chat.id,
            'CHANNEL_ID',
            '@'+channel.username
        )
        await bot.SendMessage(
            chat_id = message.chat.id,
            text = f'✅Канал добавлен\n\n▸ для прекращения наберите\n/stopoff'
        )
    except TelegramForbiddenError:
        await bot.SendMessage(
            chat_id = message.chat.id,
            text = f'⛔Бот не добавлен в администраторы данного канала!\n\n▸ Исправьте этот нюанс и попробуйте заново.'
        )


@router.message(ContentTypesFilter(content_types="any"), ChatType(chat_type=['supergroup', 'group']), CommandInMessage(command='/hello'), BotIsAdmin(), FromAdmin())
async def hello_on(message: Message, text: str, photo: Any, keyboard: list):
    db.set_greeting(message.chat.id, text, photo=photo, keyboard=';'.join(keyboard))
    await bot.SendMessage(chat_id = message.chat.id, text = '🟢Установлено приветствие:')
    if photo:
        await bot.SendPhoto(chat_id = message.chat.id, caption = text, photo=photo, reply_markup=ConvertMarkdown(keyboard))
    else: await bot.SendMessage(chat_id = message.chat.id, text = text, reply_markup=ConvertMarkdown(keyboard))


@router.message(
    ContentTypesFilter(content_types="any"),
    ChatType(chat_type=['supergroup', 'group']),
    CommandInMessage(command='/timer'),
    BotIsAdmin(),
    FromAdmin()
)
async def timer(message: Message, text: str, photo: Any, keyboard: list):
    try:
        delay = int(''.join([i for i in text if i.isdigit()]))
        text = text[len(str(delay)):]
        kb = ';'.join(keyboard)
        current_timer = db.get_chat_timer(message.chat.id)
        db.set_timer(message.chat.id, text, photo=photo, keyboard=kb, delay=delay)
        await bot.SendMessage(chat_id=message.chat.id, text=f'🟢Установлен таймер рассылки {delay} минут')
        if current_timer:
            if photo:
                await bot.SendPhoto(
                    chat_id=message.chat.id,
                    caption=text.format(name=message.from_user.first_name),
                    photo=photo,
                    reply_markup=ConvertMarkdown(kb)
                )
            else:
                await bot.SendMessage(chat_id=message.chat.id, text=text, reply_markup=ConvertMarkdown(kb))
        else:
            await create_task(
                {
                    'CHAT_ID': message.chat.id,
                    'TEXT': text,
                    'PHOTO': photo,
                    'KEYBOARD': kb,
                    'DELAY': delay
                }
            )
    except Exception as e:
        print(e)


@router.message(
    Command(commands='limit'),
    ChatType(chat_type=['supergroup', 'group']),
    BotIsAdmin(),
    FromAdmin(),
    lambda msg: msg.text.split()[-1].isdigit()
)
async def limit_on(message: Message):
    try:
        db.set_chat_value(message.chat.id, 'SYMBOL', message.text.split()[-1])
        await bot.SendMessage(
            chat_id=message.chat.id,
            text=f'🟢Установлено ограничение символов: {message.text.split()[-1]}'
        )
    except Exception as e:
        print(e)


@router.message(
    Command(commands='antiflood'),
    ChatType(chat_type=['supergroup', 'group']),
    BotIsAdmin(),
    FromAdmin(),
    lambda msg: msg.text.split()[-1].isdigit()
)
async def antiflood(message: Message):
    try:
        db.set_chat_value(message.chat.id, 'ANTIFLOOD', message.text.split()[-1])
        await bot.SendMessage(
            chat_id=message.chat.id,
            text=f'🟢Установлено ограничение сообщений: {message.text.split()[-1]}'
        )
    except Exception as e:
        print(e)


def exctract_commands(message: Message):
    options = {
        'stopoff': ('❌Канал удален!', lambda chat_id: db.set_chat_value(chat_id, 'CHANNEL_ID', None)),
        'delhello': ('🔴Приветствие удалено', lambda chat_id: db.delete_greeting(chat_id=chat_id)),
        'dellimit': ('🔴Ограничение символов отключено', lambda chat_id: db.set_chat_value(chat_id, 'SYMBOL', None)),
        'deltimer': ('🔴Рассылка удалена', lambda chat_id: db.delete_timer(chat_id)),
        'onjoin': ('🟢Удаление системных сообщений подключено', lambda chat_id: db.set_chat_value(chat_id, 'JOINED_LEFT', True)),
        'offjoin': ('🔴Удаление системных сообщений отключено', lambda chat_id: db.set_chat_value(chat_id, 'JOINED_LEFT', False)),
        'delantiflood': ('🔴Ограничение сообщений отключено', lambda chat_id: db.set_chat_value(chat_id, 'ANTIFLOOD', None)),
        'blockchannels': ('🟢Удаление сообщений от имени канала включено', lambda chat_id: db.set_chat_value(chat_id, 'BLOCK_CHANNELS', True)),
        'unblockchannels': ('🔴Удаление сообщений от имени канала отключено', lambda chat_id: db.set_chat_value(chat_id, 'BLOCK_CHANNELS', False)),
    }
    key = next((x for x in list(options.keys()) if message.text.startswith('/'+x)), None)
    return options.get(key)


@router.message(
    ChatType(chat_type='supergroup'),
    ContentTypesFilter(content_types='text'), BotIsAdmin(), FromAdmin(), lambda msg: exctract_commands(msg))
async def options_on_off(message: Message):
    data = exctract_commands(message)
    data[1](message.chat.id)
    await bot.SendMessage(chat_id=message.chat.id, text=data[0])
