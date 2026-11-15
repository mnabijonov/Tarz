
from django.db import models


class Category(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Kategoriya nomi",
    )

    name_ru = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nomi (rus tilida)",
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ikonka",
        help_text="Emoji, masalan 🚰 yoki ⚡ (Mini App'da ko'rinadi)",
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcategories",
        verbose_name="Asosiy kategoriya",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Faol",
    )

    position = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Tartib",
        help_text="Kichik raqam ro'yxatda yuqorida turadi",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt",
    )

    class Meta:
        db_table = "categories"
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ["position", "name"]

    def __str__(self):
        return f"{self.parent.name} → {self.name}" if self.parent_id else self.name

    @property
    def is_leaf(self):
        """Ichida faol xizmat turlari yo'q kategoriya: buyurtma faqat shunga beriladi."""
        return not self.subcategories.filter(is_active=True).exists()


class District(models.Model):

    name = models.CharField(
        max_length=100,
        verbose_name="Tuman",
    )

    name_ru = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nomi (rus tilida)",
    )

    city = models.CharField(
        max_length=100,
        default="Toshkent",
        verbose_name="Shahar",
    )

    class Meta:
        db_table = "districts"
        verbose_name = "Hudud"
        verbose_name_plural = "Hududlar"
        ordering = ["city", "name"]

        constraints = [
            models.UniqueConstraint(
                fields=["city", "name"],
                name="unique_district_per_city",
            )
        ]

    def __str__(self):
        return f"{self.city} - {self.name}"
