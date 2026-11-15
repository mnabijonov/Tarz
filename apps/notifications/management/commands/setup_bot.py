"""Botni Django'ga ulash (bir marta, yoki ngrok manzili o'zgarganda).

    python manage.py setup_bot https://abcd-12-34.ngrok-free.app

Nima qiladi:
  1. Telegram webhook'ini <manzil>/telegram/webhook/ ga o'rnatadi (alohida bot jarayoni kerak emas);
  2. Botdagi menyu tugmasini Mini App'ga (MINIAPP_URL yoki shu manzil) ulaydi.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.notifications.telegram import call


class Command(BaseCommand):
    help = "Telegram webhook va Mini App menyu tugmasini o'rnatadi"

    def add_arguments(self, parser):
        parser.add_argument('public_url', help="Saytning tashqi HTTPS manzili, masalan https://xxxx.ngrok-free.app")

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError(".env faylida TELEGRAM_BOT_TOKEN yo'q")

        base = options['public_url'].rstrip('/')
        if not base.startswith('https://'):
            raise CommandError("Manzil https:// bilan boshlanishi kerak (Telegram faqat HTTPS qabul qiladi)")

        webhook_ok = call('setWebhook', {
            'url': f'{base}/telegram/webhook/',
            'secret_token': settings.TELEGRAM_WEBHOOK_SECRET,
            'allowed_updates': ['message'],
            'drop_pending_updates': True,
        })
        if not webhook_ok:
            raise CommandError("Webhook o'rnatilmadi: token va internetni tekshiring")
        self.stdout.write(self.style.SUCCESS(f'Webhook: {base}/telegram/webhook/'))

        app_url = settings.MINIAPP_URL or base
        menu_ok = call('setChatMenuButton', {
            'menu_button': {'type': 'web_app', 'text': 'Tarz', 'web_app': {'url': app_url}},
        })
        if menu_ok:
            self.stdout.write(self.style.SUCCESS(f'Menyu tugmasi: {app_url}'))
        else:
            self.stdout.write(self.style.WARNING("Menyu tugmasi o'rnatilmadi"))

        if settings.MINIAPP_URL.rstrip('/') != base:
            self.stdout.write(self.style.WARNING(
                f"\n.env faylida MINIAPP_URL={base} deb yozing va serverni qayta ishga tushiring:\n"
                "bot xabarlaridagi 'Ko'rish' / 'Ilovani ochish' tugmalari shu manzildan foydalanadi."
            ))
        if base.rstrip('/') not in [f'https://{h}' for h in settings.ALLOWED_HOSTS] and '*' not in settings.ALLOWED_HOSTS:
            host = base.removeprefix('https://')
            self.stdout.write(self.style.WARNING(f".env faylida DJANGO_ALLOWED_HOSTS ga {host} ni qo'shing"))

        self.stdout.write("\nTayyor. Telegram'da botga /start yozing.")
