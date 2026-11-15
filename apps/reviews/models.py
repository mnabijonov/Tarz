from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from apps.orders.models import Order
from django.conf import settings
from apps.masters.models import MasterProfile


# Create your models here.
class Review(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviews'
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviews'
    )

    target = models.ForeignKey(
        MasterProfile,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Baho (1-5 yulduz)',
    )

    text = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='Sharh'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'author'],
                name='unique_review_per_order_author'
            )
        ]


    def __str__(self):
        return f"{self.target}--{self.rating}/5"
