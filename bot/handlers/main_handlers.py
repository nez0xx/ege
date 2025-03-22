import asyncio
from typing import Union

from aiogram import Router
from aiogram.client import bot
from aiogram.dispatcher.filters import Command, ContentTypesFilter
from aiogram.types import CallbackQuery, Message

from bot.config import db, description_2, mention_url, options, description_1
from bot.filters import BotIsAdmin, ChatType, FromAdmin, ReplyFilter
from bot.markups import (
    BackMarkup,
    ChatOptionsMarkup,
    ConvertMarkdown,
    StandartMarkup
)

router = Router()


@router.message(ContentTypesFilter(
        content_types=[
            'new_chat_title', 
            'new_chat_photo', 
            'delete_chat_photo', 
            'pinned_message'
        ]
))
async def start(message: Message):
    chat_info = db.get_chat(message.chat.id)
    if chat_info.get('BLOCK_CHANNELS'):
        return await bot.DeleteMessage(chat_id=message.chat.id, message_id=message.message_id)


@router.message(Command(commands=['start', 'info', 'help']), ChatType(chat_type='private'))
async def start(message: Message):
    user = message.from_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    await message.answer('👋', reply_markup=StandartMarkup())
    #option = db.get_reply('✅ Проверка подписки')
    '''
    await bot.SendMessage(
        chat_id=message.from_user.id,
        text=option['DESCRIPTION'],
        reply_markup=ConvertMarkdown(option['KEYBOARD'].split(';'))
    )
    '''
    await bot.SendMessage(
        chat_id=message.from_user.id,
        text=description_1,
        reply_markup=StandartMarkup()
    )


@router.message(ContentTypesFilter(content_types="text"), ChatType(chat_type='private'), ReplyFilter())
async def button(message: Message, TITLE: str, DESCRIPTION: str, PHOTO: str, KEYBOARD: str):
    option = db.get_reply(TITLE)
    if PHOTO:
        await bot.SendPhoto(
            chat_id=message.from_user.id,
            caption=DESCRIPTION,
            photo=PHOTO,
            reply_markup=ConvertMarkdown(option['KEYBOARD'].split(';'))
        )
    else:
        await bot.SendMessage(
            chat_id=message.from_user.id,
            text=DESCRIPTION,
            reply_markup=ConvertMarkdown(option['KEYBOARD'].split(';'))
        )


@router.message(
    ContentTypesFilter(content_types="text"),
    ChatType(chat_type='private'),
    lambda msg: msg.text.strip() == '⚙️Настройки чата'
)
async def option(message: Message):
    await bot.SendMessage(chat_id=message.from_user.id, text=description_2, reply_markup=ChatOptionsMarkup())


@router.message(
    ContentTypesFilter(content_types="text"),
    ChatType(chat_type='private'),
    lambda msg: msg.text.strip() == '✅Проверка подписки'
)
async def check_sub(message: Message):
    await bot.SendMessage(chat_id=message.from_user.id, text=description_1)


@router.callback_query(
    ChatType(chat_type='private'),
    lambda call: {'data': int(call.data.split('_')[-1])} if 'option_' in call.data else {'data': 'back'} if call.data == 'back' else None
)
async def callback(call: CallbackQuery, data):
    if data == 'back':
        return await bot.EditMessageText(
            text=description_2,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=ChatOptionsMarkup()
        )
    await bot.EditMessageText(
        text=list(options.items())[data][1],
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=BackMarkup()
    )


async def answer_warning(chat_id: Union[str, int], text: str, time: int):
    warning = await bot.SendMessage(chat_id=chat_id, text=text)
    await asyncio.sleep(time)
    await bot.DeleteMessage(chat_id=chat_id, message_id=warning.message_id)


@router.message(ChatType(
    chat_type=['supergroup', 'group']),
    ContentTypesFilter(
        content_types=['new_chat_members', 'left_chat_member']),
    BotIsAdmin()
)
async def handler(message: Message):
    chat_info = db.get_chat(message.chat.id)
    chat_joined_left = db.get_field('chats', 'JOINED_LEFT', 'CHAT_ID', message.chat.id)
    greeting = db.get_chat_greeting(message.chat.id)

    if greeting and message.new_chat_members:
        text, photo, keyboard = greeting['TEXT'], greeting['PHOTO'], greeting['KEYBOARD']
        for member in message.new_chat_members:
            text = text.format(name=mention_url.format(member.id, member.first_name))
            if photo:
                await bot.SendPhoto(
                    chat_id=message.chat.id,
                    caption=text.format(name=text),
                    photo=photo,
                    reply_markup=ConvertMarkdown(keyboard)
                )
            else:
                await bot.SendMessage(
                    chat_id=message.chat.id,
                    text=text.format(name=text),
                    reply_markup=ConvertMarkdown(keyboard)
                )

    if chat_info.get('BLOCK_CHANNELS'):
        return await bot.DeleteMessage(chat_id=message.chat.id, message_id=message.message_id)
    if chat_joined_left:
        if chat_joined_left.get('JOINED_LEFT'):
            await bot.DeleteMessage(
                chat_id=message.chat.id,
                message_id=message.message_id
            )


@router.message(
    ChatType(chat_type=['supergroup', 'group']),
    ContentTypesFilter(content_types=['any']),
    FromAdmin(is_admin=False),
    BotIsAdmin()
)
async def handler(message: Message):
    chat_info = db.get_chat(message.chat.id)

    channels = chat_info.get('CHANNEL_ID')
    if channels:
        channels = channels.split()
        try:
            for channel in channels:
                user = await bot.GetChatMember(chat_id=channel, user_id=message.from_user.id)
                if user.status == 'left':
                    await bot.DeleteMessage(chat_id=message.chat.id, message_id=message.message_id)

                    markup = []
                    for i in range(len(channels)):
                        markup.append(f"[➕Подпишитесь {i+1}](t.me/{channels[i][1:]})")

                    return await bot.SendMessage(
                        chat_id=message.chat.id,
                        text=f'➕{mention_url.format(message.from_user.id, message.from_user.first_name)}'
                             f', чтобы писать в этот чат, подпишитесь на каналы:\n'
                             f"{'|'.join(channels)}",
                        reply_markup=ConvertMarkdown(markup)
                        #reply_markup=ConvertMarkdown(f'[➕Подпишитесь](t.me/{channel[1:]})')
                    )

        except Exception as e:
            print(e)
    if message.forward_date:#message.forward_sender_name or message.forward_from or 
        if chat_info.get("BLOCK_FORWARD"):
            await bot.DeleteMessage(chat_id=message.chat.id, message_id=message.message_id)
            return await answer_warning(
                message.chat.id,
                f'{mention_url.format(message.from_user.id, message.from_user.first_name)}, <i>Пересылка сообщений в данном чате запрещена</i>',
                3
            )

    text = message.text or message.caption or ''
    symbol = chat_info.get('SYMBOL')
    if symbol and text:
        if len(text) > symbol:
            await bot.DeleteMessage(chat_id=message.chat.id, message_id=message.message_id)
            return await answer_warning(
                message.chat.id,
                f'{mention_url.format(message.from_user.id, message.from_user.first_name)}, <i>ваш текст не должен быть длиннее <b>{symbol}</b> символов</i>',
                3
            )
    if chat_info.get('BLOCK_CHANNELS') and message.from_user.id < 0:
        return await bot.DeleteMessage(chat_id=message.chat.id, message_id=message.message_id)

    antiflood = chat_info.get('ANTIFLOOD')
    if antiflood:
        db.add_message(message.chat.id, message.message_id, message.from_user.id)
        messages = db.get_last_messages(message.chat.id, antiflood)
        if len(messages) < antiflood:
            return
        if not all([m['FROM_USER'] == message.from_user.id for m in messages]):
            return
        if messages[0]['TIME'] - messages[-1]['TIME'] < 300:
            await bot.DeleteMessage(chat_id=message.chat.id, message_id=message.message_id)
            await answer_warning(
                message.chat.id,
                '{}, <i>не флудите</i>'.format(mention_url.format(message.from_user.id, message.from_user.first_name)),
                2
            )
