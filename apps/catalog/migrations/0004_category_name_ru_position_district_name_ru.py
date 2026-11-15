from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_alter_category_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='name_ru',
            field=models.CharField(blank=True, max_length=100, verbose_name='Nomi (rus tilida)'),
        ),
        migrations.AddField(
            model_name='category',
            name='position',
            field=models.PositiveSmallIntegerField(default=0, help_text="Kichik raqam ro'yxatda yuqorida turadi", verbose_name='Tartib'),
        ),
        migrations.AddField(
            model_name='district',
            name='name_ru',
            field=models.CharField(blank=True, max_length=100, verbose_name='Nomi (rus tilida)'),
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['position', 'name'], 'verbose_name': 'Kategoriya', 'verbose_name_plural': 'Kategoriyalar'},
        ),
    ]
