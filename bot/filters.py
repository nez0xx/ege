import re
from typing import Any, Dict, Union

from aiogram.client import bot
from aiogram.dispatcher.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from bot.config import db, markdown_link_pattern, url_pattern


class ChatType(BaseFilter):
    chat_type: Union[str, list]

    async def __call__(self, message: Union[Message, CallbackQuery]) -> bool:
        if isinstance(message, CallbackQuery):
            message = message.message
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        return message.chat.type in self.chat_type


class CommandInMessage(BaseFilter):
    command: str

    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        text = message.caption or message.text or ''
        if not text.startswith(self.command):
            return False
        text = text[len(self.command):].strip()
        photo = message.photo[-1].file_id if message.photo else None
        keyboard = [f'[{i[0]}]({i[1]})' for i in re.findall(markdown_link_pattern, text) if re.findall(url_pattern, i[1])]
        for i in keyboard:
            text = text.replace(i, '')
        return {'text': text, 'photo': photo, 'keyboard': keyboard}


class ReplyFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return db.get_reply(message.text.strip())


class BotIsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        try:
            me = await bot.GetMe()
            member = await bot.GetChatMember(chat_id=message.chat.id, user_id=me.id)
        except:
            return False
        if not db.get_chat(chat_id=message.chat.id):
            db.add_chat(chat_id=message.chat.id)
        return (member.status == 'administrator') and member.can_delete_messages


class FromAdmin(BaseFilter):
    is_admin: bool = True

    async def __call__(self, message: Message) -> bool:
        try:
            member = await bot.GetChatMember(chat_id=message.chat.id, user_id=message.from_user.id)
        except:
            return False
        return (member.status == 'administrator' or member.status == 'creator') == self.is_admin
