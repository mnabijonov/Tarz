from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from apps.catalog.models import Category, District


# Create your models here.
class MasterProfile(models.Model):

    class StatusChoice(models.TextChoices):
        PENDING = "pending", "Tasdiq kutilmoqda"
        ACCEPTED = "accepted", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="master_profile",
        verbose_name="Foydalanuvchi",
    )

    categories = models.ManyToManyField(Category, related_name="masters", verbose_name="Xizmat kategoriyalari",)
    districts = models.ManyToManyField(District, related_name="masters",verbose_name="Ish hududlari",)
    experience_years = models.PositiveSmallIntegerField(default=0, verbose_name="Tajriba (yil)",)
    bio = models.TextField(blank=True, verbose_name="Usta haqida",)

    document_photo = models.ImageField(
        upload_to="masters/documents/%Y/%m/",
        blank=True,
        verbose_name="Tasdiqlovchi hujjat",
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoice.choices,
        default=StatusChoice.PENDING,
        verbose_name="Tasdiqlash holati",
    )

    rejection_reason = models.TextField(blank=True, verbose_name="Rad etish sababi")

    rating_avg = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5),
        ],
        verbose_name="O'rtacha baho",
    )

    jobs_done = models.PositiveIntegerField(default=0, verbose_name="Yakunlangan ishlar soni")
    is_busy = models.BooleanField(default=False, verbose_name="Bandlik holati")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")



    class Meta:
        db_table = "master_profiles"
        verbose_name = "Usta profili"
        verbose_name_plural = "Usta profillari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Usta: {self.user}"


class PortfolioPhoto(models.Model):

    master = models.ForeignKey(
        MasterProfile,
        on_delete=models.CASCADE,
        related_name="portfolio_photos",
        verbose_name="Usta",
    )

    image = models.ImageField(upload_to="masters/portfolio/%Y/%m/", verbose_name="Portfolio rasmi")
    caption = models.CharField(max_length=255, blank=True, verbose_name="Rasm tavsifi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuklangan vaqt")


    class Meta:
        db_table = "master_portfolio_photos"
        verbose_name = "Portfolio rasmi"
        verbose_name_plural = "Portfolio rasmlari"
        ordering = ["-created_at"]

        

    def __str__(self):
        return f"{self.master} — portfolio #{self.pk}"
