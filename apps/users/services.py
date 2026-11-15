import hashlib, hmac, json, time
from urllib.parse import parse_qsl
from django.conf import settings


def validate_telegram_init_data(init_data):
    bot_token = settings.TELEGRAM_BOT_TOKEN

    if not bot_token:
        raise ValueError("Telegram bot token sozlanmagan")

    data = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = data.pop('hash', None)

    if not received_hash:
        raise ValueError("Telegram hash topilmadi")

    # Telegram ma'lumotlarini tartiblash
    data_check_string = '\n'.join(
        f'{key}={value}'
        for key, value in sorted(data.items())
    )

    # Telegram secret key
    secret_key = hmac.new(
        b'WebAppData',
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    # Hisoblangan hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # Hashlarni solishtirish
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Telegram ma'lumotlari haqiqiy emas")

    # Ma'lumotlarning eskirganligini tekshirish
    auth_date = int(data.get('auth_date', 0))

    if not auth_date:
        raise ValueError("auth_date mavjud emas")

    current_time = int(time.time())

    if current_time - auth_date > 86400 or auth_date > current_time + 60:
        raise ValueError("Telegram ma'lumotlari eskirgan")

    # Telegram foydalanuvchisi
    user_data = json.loads(data.get('user', '{}'))

    if not user_data.get('id'):
        raise ValueError("Telegram user ID topilmadi")

    return user_data


def telegram_profile_url(user):
    """Telegram profilini ochuvchi havola: username bo'lsa t.me, bo'lmasa tg:// ID orqali."""
    if user.telegram_username:
        return f'https://t.me/{user.telegram_username}'
    if user.telegram_id:
        return f'tg://user?id={user.telegram_id}'
    return ''


def contact_info(user):
    """Usta tanlangandan keyin ikkinchi tomonga ochiladigan kontakt ma'lumotlari."""
    return {
        'id': user.pk,
        'name': user.get_full_name() or user.username,
        'phone': user.phone,
        'telegram_id': user.telegram_id,
        'telegram_username': user.telegram_username,
        'telegram_url': telegram_profile_url(user),
    }


MAX_IMAGE_SIZE = 10 * 1024 * 1024  # PRD: bitta rasm 10 MB dan oshmaydi


def validate_image_file(value):
    from rest_framework import serializers

    if value and value.size > MAX_IMAGE_SIZE:
        raise serializers.ValidationError("Rasm hajmi 10 MB dan oshmasligi kerak.")
    return value


def ask_reason_or_run(modeladmin, request, queryset, *, action, title, submit_label, apply):
    """Admin action uchun oraliq sahifa: sabab kiritilmaguncha amal bajarilmaydi.

    apply(queryset, reason) amalni bajaradi va bajarilganlar sonini qaytaradi.
    """
    from django.contrib import messages
    from django.contrib.admin import helpers
    from django.template.response import TemplateResponse

    if request.POST.get('post') == 'yes':
        reason = (request.POST.get('reason') or '').strip()
        if reason:
            count = apply(queryset, reason)
            modeladmin.message_user(request, f"{count} ta yozuv uchun bajarildi.", messages.SUCCESS)
            return None
        modeladmin.message_user(request, "Sabab kiritilishi shart.", messages.ERROR)

    context = {
        **modeladmin.admin_site.each_context(request),
        'title': title,
        'queryset': queryset,
        'action': action,
        'submit_label': submit_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'opts': modeladmin.model._meta,
    }
    return TemplateResponse(request, 'admin/action_with_reason.html', context)


def normalize_phone(raw):
    import re
    digits = re.sub(r'\D', '', raw or '')
    return f'+{digits}' if digits else ''


def save_telegram_contact(tg_user, phone):
    """Botga kelgan telefon raqamini saqlaydi (polling bot ham, webhook ham shuni ishlatadi).

    tg_user: id, first_name, last_name, username, language_code kalitlari bor dict.
    Natija: 'ok' | 'invalid' | 'taken' | 'blocked'.
    """
    from django.db import IntegrityError, transaction

    from .models import User

    phone = normalize_phone(phone)
    telegram_id = tg_user['id']
    if not phone:
        return 'invalid'
    if User.objects.filter(phone=phone).exclude(telegram_id=telegram_id).exists():
        return 'taken'
    try:
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={'username': str(telegram_id)},
            )
            if user.is_blocked or not user.is_active:
                return 'blocked'
            if created:
                user.set_unusable_password()
                if tg_user.get('language_code') in ('uz', 'ru'):
                    user.language = tg_user['language_code']
            user.phone = phone
            user.first_name = (tg_user.get('first_name') or '')[:150]
            user.last_name = (tg_user.get('last_name') or '')[:150]
            user.telegram_username = (tg_user.get('username') or '')[:64]
            user.save()
    except IntegrityError:
        # bir vaqtda boshqa hisob shu raqamni olib qo'ygan bo'lishi mumkin
        return 'taken'
    return 'ok'


def telegram_user_state(telegram_id):
    """registered = telefon saqlangan; blocked = hisob bloklangan."""
    from .models import User

    row = User.objects.filter(telegram_id=telegram_id).values('phone', 'is_blocked', 'is_active').first()
    if not row:
        return {'registered': False, 'blocked': False}
    return {'registered': bool(row['phone']), 'blocked': bool(row['is_blocked'] or not row['is_active'])}
