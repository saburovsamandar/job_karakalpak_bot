from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton,ReplyKeyboardMarkup,KeyboardButton
from bot import user_language
from bot import *
# from lang import language
inline_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='uzbek',callback_data='lang_uz')],
        [InlineKeyboardButton(text='karakalpak',callback_data='lang_kk')],
    ]
)


def make_reply_keyboard(lang_code):

    text = language[lang_code]['vakansiya']
    reply_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text)]
        ],
        resize_keyboard=True
    )
    return reply_menu









