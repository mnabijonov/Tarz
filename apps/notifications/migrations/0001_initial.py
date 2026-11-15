import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('masters', '0002_initial'),
        ('orders', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderDispatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wave', models.PositiveSmallIntegerField(default=1, verbose_name="To'lqin")),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yuborilgan vaqt')),
                ('master', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dispatches', to='masters.masterprofile', verbose_name='Usta')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dispatches', to='orders.order', verbose_name='Buyurtma')),
            ],
            options={
                'verbose_name': 'Buyurtma tarqatmasi',
                'verbose_name_plural': 'Buyurtma tarqatmalari',
                'db_table': 'order_dispatches',
                'constraints': [models.UniqueConstraint(fields=('order', 'master'), name='unique_dispatch_per_order_master')],
            },
        ),
    ]
