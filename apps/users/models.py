from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class User(AbstractUser):

    class RoleChoice(models.TextChoices):

        CLIENT = 'client', 'Mijoz'
        MASTER = 'master', 'Usta'
        ADMIN = 'admin', 'Admin'

    class LanguageChoice(models.TextChoices):

        UZ = 'uz', 'Uzbek'
        RU = 'ru', 'Rus'

    telegram_id = models.BigIntegerField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    role = models.CharField(
        max_length=10, 
        choices=RoleChoice.choices, 
        default=RoleChoice.CLIENT
    )
    language = models.CharField(
        max_length=2, 
        choices=LanguageChoice.choices, 
        default=LanguageChoice.UZ
    )
    # Telegram @username (bo'lmasligi mumkin): tanlovdan keyin "Telegram profili" havolasi uchun
    telegram_username = models.CharField(max_length=64, blank=True, default='')
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True, default='', verbose_name='Bloklash sababi')
    blocked_at = models.DateTimeField(null=True, blank=True, verbose_name='Bloklangan vaqt')
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username or str(self.telegram_id)