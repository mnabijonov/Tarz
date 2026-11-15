from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.catalog.models import Category, District


# Create your models here.
class Order(models.Model):

    class StatusChoice(models.TextChoices):

        NEW = 'new', 'Yangi'
        SELECTED = 'selected', 'Usta tanlandi'
        IN_PROGRESS = 'in_progress', 'Jarayonda'
        COMPLETED = 'completed', 'Yakunlandi'
        CANCELLED = 'cancelled', 'Bekor qilindi'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='orders', 
        verbose_name='Mijoz'
    )
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL,
        null=True, 
        related_name='orders', 
        verbose_name='Xizmat kategoriyasi'
    )
    
    description = models.TextField(verbose_name='Buyurtma tavsifi')

    district = models.ForeignKey(
        District, 
        on_delete=models.SET_NULL,
        null=True, 
        related_name='orders', 
        verbose_name='Hudud'
    )
    
    address = models.CharField(max_length=256, blank=True, verbose_name='Manzil')

    desired_date = models.DateField(null=True, blank=True)

    budget_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    budget_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    status = models.CharField(
        max_length=20, 
        choices=StatusChoice.choices, 
        default=StatusChoice.NEW, 
        verbose_name='Buyurtma holati'
    )

    cancel_reason = models.TextField(
        blank=True,
        default="",
        verbose_name="Bekor qilish sababi",
    )

    selected_bid = models.ForeignKey(
        'bids.Bid', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='orders',
        verbose_name='Tanlangan taklif'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:

        db_table = 'orders'
        verbose_name = 'Buyurtma'
        ordering = ['-created_at']

    
    def __str__(self):
        return self.category.name if self.category else f"Buyurtma #{self.pk}"



class OrderPhoto(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Buyurtma'
        )

    image = models.ImageField(upload_to='orders/%Y/%m', verbose_name='Buyurtma rasmi')
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'order_photos'
        verbose_name = 'Buyurtma rasmi'
        ordering = ['created_at']
        

    def __str__(self):
        return f"Rasm #{self.pk} (buyurtma {self.order_id})"

