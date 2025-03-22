import asyncio
from typing import Any

from aiogram import Router, Bot
from aiogram.client import bot
from aiogram.dispatcher.filters import Command, ContentTypesFilter
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import Message

from bot.config import db
from bot.filters import BotIsAdmin, ChatType, CommandInMessage, FromAdmin
from bot.markups import ConvertMarkdown

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
            await Bot.send_message(
                chat_id=timer['CHAT_ID'],
                text=timer['TEXT'],
                reply_markup=ConvertMarkdown(timer['KEYBOARD'])
            )
        else:
            await bot.SendMessage(
                chat_id=timer['CHAT_ID'],
                text=timer['TEXT'],
                reply_markup=ConvertMarkdown(timer['KEYBOARD'])
            )
    await asyncio.sleep(timer['DELAY']*60)
    timer = db.get_chat_timer(timer['CHAT_ID'])
    if timer:
        await create_task(timer, Bot)


@router.message(
    Command(commands='add_chat'),
    ChatType(chat_type=['supergroup', 'group']),
    BotIsAdmin(),
    FromAdmin(),
    lambda msg: msg.text.replace('/add_chat', '').split('@')[-1].strip()
)
async def starton(message: Message):
    text = message.text.replace('/add_chat', '').split()
    chat_info = db.get_chat(message.chat.id)
    channels = chat_info.get('CHANNEL_ID')
    if channels is None:
        channels = []
    else:
        channels = channels.split()
    try:
        for channel_username in text:
            channel = await bot.GetChat(chat_id=channel_username)
            await bot.GetChatAdministrators(chat_id=channel.id)
            if channel_username not in channels:
                channels.append(channel_username)
        db.set_chat_value(
            message.chat.id,
            'CHANNEL_ID',
            " ".join(channels)
        )
        await bot.SendMessage(
            chat_id=message.chat.id,
            text=f'✅Каналы добавлены\n\n▸ для прекращения наберите\n/rm_chat @ник_канала'
        )
    except TelegramForbiddenError:
        await bot.SendMessage(
            chat_id=message.chat.id,
            text=f'⛔Бот не добавлен в администраторы данного канала!\n\n▸ Исправьте этот нюанс и попробуйте заново.'
        )


@router.message(
    Command(commands='rm_chat'),
    ChatType(chat_type=['supergroup', 'group']),
    BotIsAdmin(),
    FromAdmin(),
    lambda msg: msg.text.replace('/rm_chat', '').split('@')[-1].strip()
)
async def stopoff(message: Message):
    text = message.text.replace('/rm_chat', '').split()
    chat_info = db.get_chat(message.chat.id)
    channels = chat_info.get('CHANNEL_ID')
    if channels:
        channels = channels.split()
    else:
        channels = []
    if len(text) == 1 and text[0] == "all":
        db.set_chat_value(
            message.chat.id,
            'CHANNEL_ID',
            None
        )
        await bot.SendMessage(
            chat_id=message.chat.id,
            text=f'✅Каналы удалены▸ '
        )
        return
    for channel_us in text:
        if channel_us in channels:
            channels.remove(channel_us)
    db.set_chat_value(
        message.chat.id,
        'CHANNEL_ID',
        " ".join(channels)
    )
    await bot.SendMessage(
        chat_id=message.chat.id,
        text=f'✅Каналы удалены▸ '
    )


@router.message(
    Command(commands='channels'),
    ChatType(chat_type=['supergroup', 'group']),
    BotIsAdmin(),
    FromAdmin()
)
async def stopoff(message: Message):
    chat_info = db.get_chat(message.chat.id)
    channels = chat_info.get('CHANNEL_ID')
    if channels:
        channels = channels.split()
        await bot.SendMessage(
            chat_id=message.chat.id,
            text=f'Отслеживаемые каналы:\n{"\n".join(channels)}'
        )
    else:

        await bot.SendMessage(
                chat_id=message.chat.id,
                text=f'Никакие каналы не отслеживаются'
        )
@router.message(
    ContentTypesFilter(content_types="any"),
    ChatType(chat_type=['supergroup', 'group']),
    CommandInMessage(command='/set_hello'),
    BotIsAdmin(),
    FromAdmin()
)
async def hello_on(message: Message, text: str, photo: Any, keyboard: list):
    db.set_greeting(message.chat.id, text, photo=photo, keyboard=';'.join(keyboard))

    await bot.SendMessage(chat_id=message.chat.id, text = '🟢Установлено приветствие:')
    if photo:
        await bot.SendPhoto(chat_id=message.chat.id, caption=text, photo=photo, reply_markup=ConvertMarkdown(keyboard))
    else: await bot.SendMessage(chat_id=message.chat.id, text=text, reply_markup=ConvertMarkdown(keyboard))


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
    Command(commands='set_limit'),
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
    Command(commands='anti_flood'),
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
        'stopall': ('❌Каналы удалены!', lambda chat_id: db.set_chat_value(chat_id, 'CHANNEL_ID', None)),
        'del_hello': ('🔴Приветствие удалено', lambda chat_id: db.delete_greeting(chat_id=chat_id)),
        'del_limit': ('🔴Ограничение символов отключено', lambda chat_id: db.set_chat_value(chat_id, 'SYMBOL', None)),
        'del_timer': ('🔴Рассылка удалена', lambda chat_id: db.delete_timer(chat_id)),
        'on_join': ('🟢Удаление системных сообщений подключено', lambda chat_id: db.set_chat_value(chat_id, 'JOINED_LEFT', True)),
        'off_join': ('🔴Удаление системных сообщений отключено', lambda chat_id: db.set_chat_value(chat_id, 'JOINED_LEFT', False)),
        'del_antiflood': ('🔴Ограничение сообщений отключено', lambda chat_id: db.set_chat_value(chat_id, 'ANTIFLOOD', None)),
        'block_channels': ('🟢Удаление сообщений от имени канала включено', lambda chat_id: db.set_chat_value(chat_id, 'BLOCK_CHANNELS', True)),
        'unblock_channels': ('🔴Удаление сообщений от имени канала отключено', lambda chat_id: db.set_chat_value(chat_id, 'BLOCK_CHANNELS', False)),
        'forward_on': ('🟢Удаление пересылаемых сообщений включено', lambda chat_id: db.set_chat_value(chat_id, 'BLOCK_FORWARD', True)),
        'forward_off': ('🔴Удаление пересылаемых сообщений выключено', lambda chat_id: db.set_chat_value(chat_id, 'BLOCK_FORWARD', False))
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
