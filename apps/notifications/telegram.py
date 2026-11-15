"""Telegram Bot API orqali xabar yuborish (Django va Celery tomonidan, aiogram'siz).

Faqat standart kutubxona ishlatiladi, shuning uchun bot jarayoni ishlamayotgan
bo'lsa ham API xabar yubora oladi.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

API_URL = 'https://api.telegram.org/bot{token}/{method}'


class TelegramTemporaryError(Exception):
    """Tarmoq yoki 429/5xx: qayta urinish mumkin."""


def _call(method, payload, timeout=10):
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning('TELEGRAM_BOT_TOKEN sozlanmagan, xabar yuborilmadi')
        return False

    request = urllib.request.Request(
        API_URL.format(token=token, method=method),
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read()).get('ok', False)
    except urllib.error.HTTPError as exc:
        if exc.code == 429 or exc.code >= 500:
            raise TelegramTemporaryError(f'Telegram {exc.code}') from exc
        # 400/403: foydalanuvchi botni bloklagan yoki chat yo'q, qayta urinish foydasiz
        logger.info('Telegram %s xatosi (chat_id=%s): %s', exc.code, payload.get('chat_id'), exc.read()[:200])
        return False
    except (urllib.error.URLError, TimeoutError) as exc:
        raise TelegramTemporaryError(str(exc)) from exc


def open_app_button(text, path=''):
    """Mini App'ni kerakli sahifada ochuvchi inline tugma."""
    base = settings.MINIAPP_URL.rstrip('/')
    if not base:
        return None
    return {'text': text, 'web_app': {'url': f'{base}{path}'}}


def send_message(chat_id, text, button=None):
    if not chat_id:
        return False
    payload = {'chat_id': chat_id, 'text': text, 'disable_web_page_preview': True}
    if button:
        payload['reply_markup'] = {'inline_keyboard': [[button]]}
    return _call('sendMessage', payload)


def call(method, payload):
    """Istalgan Bot API metodini chaqirish (setWebhook, setChatMenuButton...). Xatoda False."""
    try:
        return _call(method, payload)
    except TelegramTemporaryError as exc:
        logger.warning('Telegram %s chaqiruvi bajarilmadi: %s', method, exc)
        return False
