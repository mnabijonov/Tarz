from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='telegram_username',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='user',
            name='block_reason',
            field=models.TextField(blank=True, default='', verbose_name='Bloklash sababi'),
        ),
        migrations.AddField(
            model_name='user',
            name='blocked_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Bloklangan vaqt'),
        ),
    ]
