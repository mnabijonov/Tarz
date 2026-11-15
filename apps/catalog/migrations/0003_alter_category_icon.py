from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_seed_catalog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='icon',
            field=models.CharField(blank=True, help_text="Emoji, masalan 🚰 yoki ⚡ (Mini App'da ko'rinadi)", max_length=100, verbose_name='Ikonka'),
        ),
    ]
