from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)
from bot.config import db, options
from typing import Union


def StandartMarkup():
    keyboard = [[KeyboardButton(text="✅Проверка подписки"), KeyboardButton(text = '⚙️Настройки чата')]]
    for button in db.get_replies():
        btn = KeyboardButton(text = button['TITLE'])
        if len(keyboard[-1])<2:
            keyboard[-1].insert(0, btn)
        else: keyboard.append([btn])
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=keyboard)


def RemoveFromStandartMarkup():
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    replies = db.get_replies()
    for ind, button in enumerate(db.get_replies(), start=1):
        btn = InlineKeyboardButton(text=button['TITLE'], callback_data=f'remove_{ind}')
        markup.inline_keyboard.append([btn])
    return markup


def ChatOptionsMarkup():
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for ind, title in enumerate(list(options.keys())):
        markup.inline_keyboard.append([InlineKeyboardButton(text=title, callback_data='option_'+str(ind))])
    return markup


def BackMarkup():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔙 Назад', callback_data='back')]])


def ConvertMarkdown(buttons: Union[str, list]):
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    if isinstance(buttons, str):
        buttons = buttons.split(';')
    btns_list = [[]]
    for button in buttons:
        if not len(button.strip()):
            continue
        text, url = button[1:-1].split('](')
        if len(btns_list[-1]) < 2:
            btns_list[-1].append(InlineKeyboardButton(text=text, url=url))
        else:
            btns_list.append([InlineKeyboardButton(text=text, url=url)])

    for row in btns_list:

        markup.inline_keyboard.append(row)
    return markup
