import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import CommandStart
from config import BotToken, ADMINS, CHANNEL_ID
from lang import language
from datetime import datetime

# --- Bot va Dispatcher ---
bot = Bot(token=BotToken)
dp = Dispatcher()

# --- Inline va Reply menyular ---
inline_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🇺🇿 Uzbek tili', callback_data='lang_uz')],
        [InlineKeyboardButton(text='🇬🇦 Qaraqalpaq tili', callback_data='lang_kk')],
        [InlineKeyboardButton(text='🇷🇺 русский язык', callback_data='lang_ru')],
    ]
)

def make_reply_keyboard(lang_code):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=language[lang_code]['vakansiya'])]],
        resize_keyboard=True
    )

# --- Ma'lumotlar saqlovchilari ---
user_language = {}      # {user_id: 'uz'/'kk'}
user_data = {}          # {user_id: {...}}
waiting_for_admin = {}  # foydalanuvchi ma’lumotlari admin tasdiqlash uchun

# --- /start ---
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        f"{message.from_user.first_name}, Iltimas tildi saylań | iltimos tilni tanlang \n пожалуйста , выберите язык 👇",
        reply_markup=inline_menu
    )

# --- Til tanlash ---
@dp.callback_query(F.data.startswith('lang_'))
async def set_language(callback: CallbackQuery):
    lang_code = callback.data.split('_')[1]
    uid = callback.from_user.id
    user_language[uid] = lang_code
    await callback.message.delete()
    await callback.message.answer(language[lang_code]['chosen'], reply_markup=make_reply_keyboard(lang_code))
    await callback.answer()

# --- Vakansiya qo‘shish ---
@dp.message(F.text.in_([language['uz']['vakansiya'], language['kk']['vakansiya'],language['ru']['vakansiya']]))
async def start_vacancy(message: Message):
    uid = message.from_user.id
    lang = user_language.get(uid)
    if not lang:
        await message.answer("Iltimos, avval tilni tanlang.")
        return
    user_data[uid] = {'step': 'position', 'lang': lang, 'is_admin': uid in ADMINS}
    await message.answer(language[lang]['questions'][0], reply_markup=ReplyKeyboardRemove())

# --- Ma'lumotlarni ketma-ket olish ---
@dp.message()
async def collect_info(message: Message):
    uid = message.from_user.id
    if uid not in user_data:
        return
    data = user_data[uid]
    lang = data['lang']
    step = data['step']

    steps = ['position', 'organization', 'address', 'requirements', 'working_hours', 'salary', 'contacts', 'additional']
    current_index = steps.index(step)
    data[step] = message.text

    if current_index < len(steps) - 1:
        data['step'] = steps[current_index + 1]
        await message.answer(language[lang]['questions'][current_index + 1])
    else:
        await show_user_preview(message, data, lang)

# --- Foydalanuvchiga yakuniy ko‘rinish ---
async def show_user_preview(message: Message, data, lang):
    text = language[lang]['info_text'].format(**data)
    if data.get('is_admin'):  # Admin vakansiyasi
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Kanalǵa jaylaw", callback_data=f"admin_self_approve_{message.from_user.id}")],
                [InlineKeyboardButton(text="❌ Bıykarlaw", callback_data=f"admin_self_cancel_{message.from_user.id}")]
            ]
        )
    else:  # Foydalanuvchi vakansiyasi
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=language[lang]['send'], callback_data='user_send')],
                [InlineKeyboardButton(text=language[lang]['fill'], callback_data='restart')]
            ]
        )
    await message.answer(text, reply_markup=markup)

# --- Foydalanuvchi “Yuborish” bosganda (adminlarga yuboriladi) ---
@dp.callback_query(F.data == "user_send")
async def user_send(callback: CallbackQuery):
    uid = callback.from_user.id
    data = user_data.get(uid)
    if not data:
        await callback.message.answer("❗️ Ma'lumot topilmadi, qaytadan boshlang.")
        return

    text = language[data['lang']]['info_text'].format(**data)
    markup_admin = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Kanalǵa jaylaw", callback_data=f"admin_approve_{uid}")],
            [InlineKeyboardButton(text="❌ Bıykarlaw", callback_data=f"admin_cancel_{uid}")]
        ]
    )

    # Faqat adminlarga yuboriladi
    for admin_id in ADMINS:
        text = language[data['lang']]['info_text'].format(**data)
        clean_text = ''
        if "✅ Siz kirgizgen maǵlıwmatlar:\n\n" in text:
            clean_text = text.replace("✅ Siz kirgizgen maǵlıwmatlar:\n\n", "")
        elif "✅ Siz kiritgan maʼlumotlar:\n\n" in text:
            clean_text = text.replace("✅ Siz kiritgan maʼlumotlar:\n\n", "")
        elif "✅ Введенные вами данные:\n\n" in text:
            clean_text = text.replace("✅ Введенные вами данные:\n\n", "")   
            # uz lang 
        if "Lavozim:" in clean_text:
            clean_text = clean_text.replace("Lavozim:", "<b>👨‍💼 Lawazım:</b>")
            clean_text = clean_text.replace("Tashkilot:", "<b>🏛 Mekeme:</b>")
            clean_text = clean_text.replace("Manzil:", "<b>📍 Mánzil:</b>")
            clean_text = clean_text.replace("Aloqalar:", "<b>☎️ Baylanıs:</b>")
            clean_text = clean_text.replace("Ish haqi:", "<b>💰 Aylıq:</b>")
            clean_text = clean_text.replace("Ish vaqti:", "<b>⏰ Jumıs waqıtı:</b>")
            clean_text = clean_text.replace("Talablar:", "<b>📌 Talaplar:</b>")
            clean_text = clean_text.replace("Qo'shimcha:", "<b>📎Qosımsha:</b>")
        elif "Должность" in clean_text:
            clean_text = clean_text.replace("Должность:", "<b>👨‍💼 Lawazım:</b>")
            clean_text = clean_text.replace("Организация:", "<b>🏛 Mekeme:</b>")
            clean_text = clean_text.replace("Местонахождение:", "<b>📍 Mánzil:</b>")
            clean_text = clean_text.replace("Требования:", "<b>📌 Talaplar:</b>")
            clean_text = clean_text.replace("Час работы:", "<b>⏰ Jumıs waqıtı:</b>")
            clean_text = clean_text.replace("Контакты:", "<b>☎️ Baylanıs:</b>")
            clean_text = clean_text.replace("Зарплата:", "<b>💰 Aylıq:</b>")
            clean_text = clean_text.replace("Дополнительные:", "<b>📎Qosımsha:</b>")
        print(clean_text)
        await bot.send_message(admin_id, f"📥 Jańa vakansiya keldi:\n\n{clean_text}", reply_markup=markup_admin,parse_mode="HTML")

    waiting_for_admin[uid] = data.copy()
    await callback.message.delete()
    await callback.message.answer(f"{language[data['lang']]['final_send']}", reply_markup=make_reply_keyboard(data['lang']))
    del user_data[uid]

# --- Admin (foydalanuvchi vakansiyasi) tasdiqlasa ---
@dp.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve(callback: CallbackQuery):
    uid = int(callback.data.split("_")[-1])
    data = waiting_for_admin.get(uid)
    if not data:
        await callback.answer("❗️ Maǵlıwmat tabılmadı yamasa álleqashan qayta islengen.", show_alert=True)
        return

    text = language[data['lang']]['info_text'].format(**data)
    clean_text = ''
    if "✅ Siz kirgizgen maǵlıwmatlar:\n\n" in text:
        clean_text = text.replace("✅ Siz kirgizgen maǵlıwmatlar:\n\n", "")
    elif "✅ Siz kiritgan maʼlumotlar:\n\n" in text:
        clean_text = text.replace("✅ Siz kiritgan maʼlumotlar:\n\n", "")
    elif "✅ Введенные вами данные:\n\n" in text:
        clean_text = text.replace("✅ Введенные вами данные:\n\n", "")
        # uz lang 
    if "Lavozim:" in clean_text:
        clean_text = clean_text.replace("Lavozim:", "<b>👨‍💼 Lawazım:</b>")
        clean_text = clean_text.replace("Tashkilot:", "<b>🏛 Mekeme:</b>")
        clean_text = clean_text.replace("Manzil:", "<b>📍 Mánzil:</b>")
        clean_text = clean_text.replace("Aloqalar:", "<b>☎️ Baylanıs:</b>")
        clean_text = clean_text.replace("Ish haqi:", "<b>💰 Aylıq:</b>")
        clean_text = clean_text.replace("Ish vaqti:", "<b>⏰ Jumıs waqıtı:</b>")
        clean_text = clean_text.replace("Talablar:", "<b>📌 Talaplar:</b>")
        clean_text = clean_text.replace("Qo'shimcha:", "<b>📎Qosımsha:</b>")
    elif "Должность" in clean_text:
        clean_text = clean_text.replace("Должность:", "<b>👨‍💼 Lawazım:</b>")
        clean_text = clean_text.replace("Организация:", "<b>🏛 Mekeme:</b>")
        clean_text = clean_text.replace("Местонахождение:", "<b>📍 Mánzil:</b>")
        clean_text = clean_text.replace("Требования:", "<b>📌 Talaplar:</b>")
        clean_text = clean_text.replace("Час работы:", "<b>⏰ Jumıs waqıtı:</b>")
        clean_text = clean_text.replace("Контакты:", "<b>☎️ Baylanıs:</b>")
        clean_text = clean_text.replace("Зарплата:", "<b>💰 Aylıq:</b>")
        clean_text = clean_text.replace("Дополнительные:", "<b>📎Qosımsha:</b>")
    print(clean_text)
    await bot.send_message(CHANNEL_ID, f"<b>📢 DIQQAT, TAZA VAKANCIYA!</b>\n\n{clean_text}\n\n\n<b>📅 Jaylastırılǵan sáne:</b>  {datetime.now().strftime("%Y.%m.%d")}",parse_mode="HTML")

    await callback.message.delete()
    await bot.send_message(uid, f"{language[data['lang']]['approved']}", reply_markup=make_reply_keyboard(data['lang']))
    del waiting_for_admin[uid]

# --- Admin (foydalanuvchi vakansiyasi) bekor qilsa ---
@dp.callback_query(F.data.startswith("admin_cancel_"))
async def admin_cancel(callback: CallbackQuery):
    uid = int(callback.data.split("_")[-1])
    data = waiting_for_admin.get(uid)
    await callback.message.delete()
    lang = user_language.get(callback.from_user.id, 'uz')
    await callback.message.answer("❌ Vakansiya biykar etildi.", reply_markup=make_reply_keyboard(lang))
    if data:
        await bot.send_message(uid, f"{language[data['lang']]['rejected']}", reply_markup=make_reply_keyboard(data['lang']))
        del waiting_for_admin[uid]

# --- Admin (o‘zi vakansiya qo‘shgan) tasdiqlasa ---
@dp.callback_query(F.data.startswith("admin_self_approve_"))
async def admin_self_approve(callback: CallbackQuery):
    uid = int(callback.data.split("_")[-1])
    data = user_data.get(uid)
    if not data:
        await callback.answer("❗️ Maǵlıwmat tabılmadı.", show_alert=True)
        return

    # Admin vakansiyasi uchun alohida text
    clean_text = (
        f"<b>👨‍💼 Lawazım:</b> {data['position']}\n"
        f"<b>🏛 Mekeme:</b> {data['organization']}\n"
        f"<b>📍 Mánzil:</b> {data['address']}\n"
        f"<b>📌 Talaplar:</b> {data['requirements']}\n"
        f"<b>⏰ Jumıs waqıtı:</b> {data['working_hours']}\n"
        f"<b>💰 Aylıq:</b> {data['salary']}\n"
        f"<b>☎️ Baylanıs:</b> {data['contacts']}\n"
        f"<b>📎Qosımsha:</b> {data['additional']}"
    )

    await bot.send_message(CHANNEL_ID, f"<b>📢 DIQQAT, TAZA VAKANCIYA!</b> \n\n{clean_text}\n\n\n<b>📅 Jaylastırılǵan sáne:</b>  {datetime.now().strftime("%Y.%m.%d")}",parse_mode="HTML")
    await callback.message.delete()
    await callback.message.answer("✅ Vakansiya kanalǵa jaylastırıldı!", reply_markup=make_reply_keyboard(data['lang']))
    del user_data[uid]

# --- Admin (o‘zi vakansiya qo‘shgan) bekor qilsa ---
@dp.callback_query(F.data.startswith("admin_self_cancel_"))
async def admin_self_cancel(callback: CallbackQuery):
    uid = int(callback.data.split("_")[-1])
    data = user_data.get(uid)
    await callback.message.delete()
    if data:
        await callback.message.answer("❌ Vakansiya biykar etildi.", reply_markup=make_reply_keyboard(data['lang']))
        del user_data[uid]

# --- Qayta to‘ldirish ---
@dp.callback_query(F.data == "restart")
async def restart_form(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = user_language.get(uid, 'uz')
    await callback.message.delete()
    user_data[uid] = {'step': 'position', 'lang': lang, 'is_admin': uid in ADMINS}
    await callback.message.answer(language[lang]['questions'][0], reply_markup=ReplyKeyboardRemove())

# --- Botni ishga tushirish ---
async def main():
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
