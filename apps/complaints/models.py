
from django.db import models
from django.conf import settings
from apps.orders.models import Order


class Complaint(models.Model):

    class StatusChoice(models.TextChoices):
        OPEN = "open", "Ochiq"
        RESOLVED = "resolved", "Yopilgan"



    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
    )

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=StatusChoice.choices,
        default=StatusChoice.OPEN,
    )

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_complaints",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.author or 'Noma’lum foydalanuvchi'}"
