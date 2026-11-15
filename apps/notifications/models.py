from django.db import models


class OrderDispatch(models.Model):
    """Buyurtma qaysi ustaga, qaysi to'lqinda yuborilganini saqlaydi (qayta yubormaslik uchun)."""

    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='dispatches',
        verbose_name='Buyurtma',
    )
    master = models.ForeignKey(
        'masters.MasterProfile',
        on_delete=models.CASCADE,
        related_name='dispatches',
        verbose_name='Usta',
    )
    wave = models.PositiveSmallIntegerField(default=1, verbose_name="To'lqin")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yuborilgan vaqt')

    class Meta:
        db_table = 'order_dispatches'
        verbose_name = 'Buyurtma tarqatmasi'
        verbose_name_plural = 'Buyurtma tarqatmalari'
        constraints = [
            models.UniqueConstraint(fields=['order', 'master'], name='unique_dispatch_per_order_master'),
        ]

    def __str__(self):
        return f'Buyurtma #{self.order_id} -> {self.master} ({self.wave}-to\'lqin)'
