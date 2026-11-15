from django.db import models
from apps.orders.models import Order
from apps.masters.models import MasterProfile


# Create your models here.
class Bid(models.Model):

    class StatusChoice(models.TextChoices):

        PENDING = 'pending', 'Jarayonda'
        ACCEPTED = 'accepted', 'Qabul qilindi'
        REJECTED = 'rejected', 'Rad etildi'

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name='Buyurtmaga taklif'
    )

    master = models.ForeignKey(
        MasterProfile,
        on_delete=models.CASCADE,
        related_name='bids',
    )

    price = models.DecimalField(max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField(verbose_name='bajarish muddati')
    comments = models.TextField(blank=True, null=True, verbose_name='Usta izohi')

    status = models.CharField(
            max_length=20,
            choices=StatusChoice.choices,
            default=StatusChoice.PENDING,
            verbose_name="Tasdiqlash holati",
        )

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'master'],
                name='unique_master_bid_per_order'
            )
        ]


    def __str__(self):
        return f"Taklif #{self.pk} - {self.price}"