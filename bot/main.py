"""Bot: polling rejimi (ixtiyoriy).

Oddiy holatda bot Django ichida webhook orqali ishlaydi (python manage.py setup_bot <url>),
bu faylni ishga tushirish shart emas. Webhook'siz (masalan HTTPS manzil yo'q) sinash uchun:
    python bot/main.py
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    MenuButtonWebApp,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from asgiref.sync import sync_to_async
from django.conf import settings
from apps.users.services import save_telegram_contact, telegram_user_state

dp = Dispatcher()

WELCOME = (
    "Tarz: Toshkentda tekshirilgan usta topish. Buyurtma qoldiring, ustalar narx taklif qiladi, siz tanlaysiz.\n\n"
    "Boshlash uchun pastdagi tugma orqali ilovani oching."
)


@sync_to_async
def get_user_state(telegram_id):
    return telegram_user_state(telegram_id)


@sync_to_async
def save_contact(tg_user, phone):
    return save_telegram_contact(
        {
            'id': tg_user.id,
            'first_name': tg_user.first_name,
            'last_name': tg_user.last_name,
            'username': tg_user.username,
            'language_code': tg_user.language_code,
        },
        phone,
    )


def open_app_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='Tarz ilovasini ochish', web_app=WebAppInfo(url=settings.MINIAPP_URL))
    ]])


def contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='Telefon raqamimni ulashish', request_contact=True)]],
        resize_keyboard=True,
    )


async def set_app_menu(bot: Bot, chat_id: int):
    """Chatdagi menyu tugmasi har doim Mini App'ni ochadi (telefon ilova ichida so'raladi)."""
    if not settings.MINIAPP_URL:
        return
    try:
        await bot.set_chat_menu_button(
            chat_id=chat_id,
            menu_button=MenuButtonWebApp(text='Tarz', web_app=WebAppInfo(url=settings.MINIAPP_URL)),
        )
    except Exception:
        logging.exception("Menyu tugmasini o'rnatib bo'lmadi")


@dp.message(CommandStart())
async def on_start(message: Message, bot: Bot):
    state = await get_user_state(message.from_user.id)
    if state['blocked']:
        await message.answer("Hisobingiz bloklangan. Yordam uchun admin bilan bog'laning.")
        return
    await set_app_menu(bot, message.chat.id)
    await message.answer(WELCOME, reply_markup=open_app_keyboard())


@dp.message(Command('phone'))
async def on_phone_command(message: Message):
    """Zaxira yo'l: eski Telegram versiyasida ilova ichidan raqam so'rab bo'lmasa."""
    await message.answer(
        "Telefon raqamingizni ulashish uchun pastdagi tugmani bosing.",
        reply_markup=contact_keyboard(),
    )


@dp.message(F.contact)
async def on_contact(message: Message, bot: Bot):
    contact = message.contact

    if contact.user_id != message.from_user.id:
        await message.answer("Iltimos, o'zingizning raqamingizni ulashing.", reply_markup=contact_keyboard())
        return

    result = await save_contact(message.from_user, contact.phone_number)
    if result == 'taken':
        await message.answer("Bu raqam boshqa hisobga biriktirilgan. Yordam uchun admin bilan bog'laning.")
        return
    if result == 'blocked':
        await message.answer("Hisobingiz bloklangan. Yordam uchun admin bilan bog'laning.")
        return
    if result != 'ok':
        await message.answer("Raqamni o'qib bo'lmadi. Qayta urinib ko'ring.", reply_markup=contact_keyboard())
        return

    # Raqam Mini App ichidagi "Telefon raqamimni ulashish" tugmasidan ham shu yerga keladi.
    await message.answer("Raqamingiz saqlandi ✅", reply_markup=ReplyKeyboardRemove())
    await set_app_menu(bot, message.chat.id)
    await message.answer("Ilovaga qaytishingiz mumkin.", reply_markup=open_app_keyboard())


@dp.message()
async def on_other(message: Message, bot: Bot):
    state = await get_user_state(message.from_user.id)
    if state['blocked']:
        await message.answer("Hisobingiz bloklangan. Yordam uchun admin bilan bog'laning.")
        return
    await message.answer("Ilovani ochish uchun tugmani bosing.", reply_markup=open_app_keyboard())


async def main():
    token = settings.TELEGRAM_BOT_TOKEN
    
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=token)
    # Webhook (python manage.py setup_bot) o'rnatilgan bo'lsa polling ishlamaydi: o'chirib qo'yamiz.
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())