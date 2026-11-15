"""Bot orqali bildirishnomalar va buyurtmani tarqatish (Celery vazifalari).

PRD "Buyurtmani tarqatish mantiqi":
  1. Kategoriya va tumani mos, tasdiqlangan, band bo'lmagan ustalar tanlanadi.
  2. Reyting va oxirgi faollik bo'yicha saralanib, 1-to'lqinda 15 ta ustaga yuboriladi.
  3. 30 daqiqada 2 tadan kam taklif kelsa, keyingi 15 ta ustaga yuboriladi.
  4. 2 soatda taklif bo'lmasa, admin'ga ogohlantirish boradi.
"""
import logging

from celery import shared_task
from django.conf import settings
from django.db.models import F

from apps.masters.models import MasterProfile
from apps.orders.models import Order
from apps.users.models import User
from apps.users.services import telegram_profile_url

from .models import OrderDispatch
from .telegram import TelegramTemporaryError, open_app_button, send_message

logger = logging.getLogger(__name__)


def _money(value):
    return f"{int(value):,}".replace(',', ' ') + " so'm"


def _order_summary(order):
    lines = [
        f"Xizmat: {order.category if order.category else '-'}",
        f"Tuman: {order.district.name if order.district else '-'}",
    ]
    if order.desired_date:
        lines.append(f"Sana: {order.desired_date:%d.%m.%Y}")
    if order.budget_min is not None or order.budget_max is not None:
        low = _money(order.budget_min) if order.budget_min is not None else '...'
        high = _money(order.budget_max) if order.budget_max is not None else '...'
        lines.append(f"Byudjet: {low} - {high}")
    description = order.description if len(order.description) <= 300 else order.description[:300] + '...'
    lines.append('')
    lines.append(description)
    return '\n'.join(lines)


@shared_task(
    autoretry_for=(TelegramTemporaryError,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=5,
)
def send_telegram_message(chat_id, text, button=None):
    """Bitta xabar = bitta vazifa: xato bo'lsa faqat shu xabar qayta yuboriladi."""
    return send_message(chat_id, text, button)


def eligible_masters(order):
    # Kategoriya yoki tuman o'chirilgan bo'lsa (SET_NULL), hech kimga yubormaymiz:
    # aks holda `categories=None` kategoriyasiz ustalarni tanlab qo'yadi.
    if not order.category_id or not order.district_id:
        return MasterProfile.objects.none()
    return (
        MasterProfile.objects.filter(
            status=MasterProfile.StatusChoice.ACCEPTED,
            is_busy=False,
            categories__in=[c for c in (order.category_id, order.category.parent_id) if c],
            districts=order.district_id,
            user__role=User.RoleChoice.MASTER,
            user__is_active=True,
            user__is_blocked=False,
            user__telegram_id__isnull=False,
        )
        .exclude(user_id=order.client_id)
        .exclude(dispatches__order=order)
        .exclude(bids__order=order)
        .select_related('user')
        .distinct()
        .order_by('-rating_avg', F('user__last_login').desc(nulls_last=True), 'pk')
    )


def enqueue(task, *args, countdown=None):
    """Vazifani navbatga qo'yadi. Redis ishlamasa ham API so'rovi yiqilmasin: xato faqat logga yoziladi."""
    if countdown and settings.CELERY_TASK_ALWAYS_EAGER:
        # Celery'siz rejimda kechiktirilgan vazifani darhol bajarish noto'g'ri bo'lardi
        # (masalan, admin'ga "2 soatdan beri taklifsiz" xabari darhol ketardi): o'tkazib yuboramiz.
        logger.info('Celery worker yo\'q, taymerli vazifa o\'tkazib yuborildi: %s%s', task.name, args)
        return
    try:
        task.apply_async(args, countdown=countdown)
    except Exception:
        logger.exception('Vazifani navbatga qo\'yib bo\'lmadi: %s%s', task.name, args)


def schedule_order_dispatch(order_id):
    """Buyurtma yaratilgach chaqiriladi (transaction.on_commit ichida)."""
    enqueue(dispatch_order, order_id, 1)
    enqueue(alert_admins_no_bids, order_id, countdown=settings.NO_BID_ADMIN_ALERT_DELAY)


@shared_task
def dispatch_order(order_id, wave=1):
    order = Order.objects.select_related('category__parent', 'district').filter(pk=order_id).first()
    if order is None or order.status != Order.StatusChoice.NEW:
        return 0

    masters = list(eligible_masters(order)[:settings.DISPATCH_WAVE_SIZE])
    created = OrderDispatch.objects.bulk_create(
        [OrderDispatch(order=order, master=m, wave=wave) for m in masters],
        ignore_conflicts=True,
    )

    text = f"Yangi buyurtma #{order.pk}\n\n{_order_summary(order)}"
    button = open_app_button("Ko'rish", f'/orders/{order.pk}')
    for master in masters:
        send_telegram_message.delay(master.user.telegram_id, text, button)

    if wave == 1:
        enqueue(check_second_wave, order_id, countdown=settings.DISPATCH_SECOND_WAVE_DELAY)

    logger.info('Buyurtma #%s: %s-to\'lqinda %s ta ustaga yuborildi', order_id, wave, len(created))
    return len(masters)


@shared_task
def check_second_wave(order_id):
    order = Order.objects.filter(pk=order_id, status=Order.StatusChoice.NEW).first()
    if order is None:
        return 0
    if order.bids.count() >= settings.DISPATCH_SECOND_WAVE_MIN_BIDS:
        return 0
    return dispatch_order(order_id, 2)


@shared_task
def alert_admins_no_bids(order_id):
    order = Order.objects.select_related('category', 'district').filter(
        pk=order_id, status=Order.StatusChoice.NEW,
    ).first()
    if order is None or order.bids.exists():
        return False

    text = (
        f"⚠️ Buyurtma #{order.pk} 2 soatdan beri taklifsiz.\n"
        f"Admin panelda ustani qo'lda biriktiring.\n\n{_order_summary(order)}"
    )
    for chat_id in settings.ADMIN_TELEGRAM_IDS:
        send_telegram_message.delay(chat_id, text)
    return True


@shared_task
def notify_bid_selected(order_id):
    """Tanlangan ustaga mijoz kontakti, qolgan ustalarga "boshqa usta tanlandi" (M6)."""
    order = Order.objects.select_related(
        'client', 'category', 'selected_bid__master__user',
    ).filter(pk=order_id).first()
    if order is None or order.selected_bid is None:
        return

    selected_master = order.selected_bid.master
    client = order.client
    lines = [
        f"🎉 Mijoz sizni buyurtma #{order.pk} uchun tanladi!",
        '',
        _order_summary(order),
        '',
        f"Mijoz: {client.get_full_name() or client.username}",
        f"Telefon: {client.phone or '-'}",
    ]
    if order.address:
        lines.append(f"Manzil: {order.address}")
    telegram = telegram_profile_url(client)
    if telegram.startswith('https://'):
        lines.append(f"Telegram: {telegram}")
    send_telegram_message.delay(
        selected_master.user.telegram_id,
        '\n'.join(lines),
        open_app_button('Ishni ochish', f'/jobs/{order.pk}'),
    )

    other_chat_ids = (
        order.bids.exclude(pk=order.selected_bid_id)
        .values_list('master__user__telegram_id', flat=True)
    )
    for chat_id in other_chat_ids:
        send_telegram_message.delay(
            chat_id,
            f"Buyurtma #{order.pk} bo'yicha mijoz boshqa ustani tanladi. Taklifingiz uchun rahmat!",
        )


@shared_task
def notify_order_cancelled(order_id):
    order = Order.objects.select_related('selected_bid__master__user').filter(pk=order_id).first()
    if order is None or order.selected_bid is None:
        return
    text = f"Mijoz buyurtma #{order.pk} ni bekor qildi."
    if order.cancel_reason:
        text += f"\nSabab: {order.cancel_reason}"
    send_telegram_message.delay(order.selected_bid.master.user.telegram_id, text)


@shared_task
def notify_master_status(master_id):
    """Admin ustani tasdiqlagan yoki rad etganda ustaga xabar (U2)."""
    profile = MasterProfile.objects.select_related('user').filter(pk=master_id).first()
    if profile is None:
        return
    S = MasterProfile.StatusChoice
    if profile.status == S.ACCEPTED:
        text = "✅ Profilingiz tasdiqlandi! Endi mos buyurtmalar shu botga keladi."
        button = open_app_button('Buyurtmalarni ko\'rish', '/feed')
    elif profile.status == S.REJECTED:
        text = "❌ Profilingiz rad etildi."
        if profile.rejection_reason:
            text += f"\nSabab: {profile.rejection_reason}"
        text += "\nMa'lumotlarni to'g'rilab, qayta yuborishingiz mumkin."
        button = open_app_button('Profilni ochish', '/master/profile')
    else:
        return
    send_telegram_message.delay(profile.user.telegram_id, text, button)
