import django.core.validators
from django.db import migrations, models


def round_existing_ratings(apps, schema_editor):
    """Eski o'nli baholarni 1-5 oralig'idagi butun songa keltiradi."""
    Review = apps.get_model('reviews', 'Review')
    for review in Review.objects.all():
        value = int(round(float(review.rating or 0)))
        review.rating = min(max(value, 1), 5)
        review.save(update_fields=['rating'])


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(round_existing_ratings, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='review',
            name='rating',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Baho (1-5 yulduz)'),
        ),
    ]
