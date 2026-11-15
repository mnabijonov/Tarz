"""Telegram bot Django ichida (webhook rejimi).

Telegram har bir xabarni POST /telegram/webhook/ ga yuboradi. Alohida bot jarayoni kerak emas:
`python manage.py runserver` + bir martalik `python manage.py setup_bot <https-manzil>` yetarli.
(bot/main.py polling rejimi ham ishlaydi, lekin ikkalasi bir vaqtda ishlamaydi.)
"""
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.users.services import save_telegram_contact, telegram_user_state

from .telegram import call, open_app_button

logger = logging.getLogger(__name__)

WELCOME = (
    "Tarz: Toshkentda tekshirilgan usta topish. Buyurtma qoldiring, ustalar narx taklif qiladi, siz tanlaysiz.\n\n"
    "Boshlash uchun pastdagi tugma orqali ilovani oching."
)
BLOCKED = "Hisobingiz bloklangan. Yordam uchun admin bilan bog'laning."


def _send(chat_id, text, reply_markup=None):
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    call('sendMessage', payload)


def _open_app_markup():
    button = open_app_button('Tarz ilovasini ochish')
    return {'inline_keyboard': [[button]]} if button else None


def _set_chat_menu(chat_id):
    """Shu chatdagi menyu tugmasini Mini App'ga ulaydi (eski bot qo'ygan "Menu" ni almashtiradi)."""
    if settings.MINIAPP_URL:
        call('setChatMenuButton', {
            'chat_id': chat_id,
            'menu_button': {'type': 'web_app', 'text': 'Tarz', 'web_app': {'url': settings.MINIAPP_URL}},
        })


def _contact_markup():
    return {
        'keyboard': [[{'text': 'Telefon raqamimni ulashish', 'request_contact': True}]],
        'resize_keyboard': True,
        'one_time_keyboard': True,
    }


def handle_message(message):
    chat_id = message['chat']['id']
    sender = message.get('from') or {}
    text = (message.get('text') or '').strip()

    if message['chat'].get('type') != 'private' or not sender.get('id'):
        return

    # Telefon raqami: Mini App'dagi "Telefon raqamimni ulashish" yoki /phone tugmasidan keladi
    contact = message.get('contact')
    if contact:
        if contact.get('user_id') != sender['id']:
            _send(chat_id, "Iltimos, o'zingizning raqamingizni ulashing.", _contact_markup())
            return
        result = save_telegram_contact(sender, contact.get('phone_number'))
        if result == 'taken':
            _send(chat_id, "Bu raqam boshqa hisobga biriktirilgan. Yordam uchun admin bilan bog'laning.")
        elif result == 'blocked':
            _send(chat_id, BLOCKED)
        elif result != 'ok':
            _send(chat_id, "Raqamni o'qib bo'lmadi. Qayta urinib ko'ring.", _contact_markup())
        else:
            _send(chat_id, "Raqamingiz saqlandi ✅", {'remove_keyboard': True})
            _send(chat_id, "Ilovaga qaytishingiz mumkin.", _open_app_markup())
        return

    if telegram_user_state(sender['id'])['blocked']:
        _send(chat_id, BLOCKED)
        return

    if text.startswith('/phone'):
        _send(chat_id, "Telefon raqamingizni ulashish uchun pastdagi tugmani bosing.", _contact_markup())
    elif text.startswith('/start'):
        _set_chat_menu(chat_id)
        _send(chat_id, WELCOME, _open_app_markup())
    else:
        _send(chat_id, "Ilovani ochish uchun tugmani bosing.", _open_app_markup())


@csrf_exempt
@require_POST
def telegram_webhook(request):
    # Telegram setWebhook'dagi secret_token'ni har so'rovda shu sarlavhada yuboradi
    received = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    if not settings.TELEGRAM_WEBHOOK_SECRET or not hmac.compare_digest(received, settings.TELEGRAM_WEBHOOK_SECRET):
        return HttpResponseForbidden()

    try:
        update = json.loads(request.body)
        message = update.get('message')
        if message:
            handle_message(message)
    except Exception:
        # Telegram 200 olmasa, xabarni qayta-qayta yuboradi: xatoni logga yozib, baribir 200 qaytaramiz
        logger.exception('Telegram update qayta ishlanmadi')
    return HttpResponse('ok')
