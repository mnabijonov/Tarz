"""Boshlang'ich ma'lumotlar: Toshkent tumanlari va 8 ta kategoriya.

Admin panelda istalgancha o'zgartirish mumkin. Mavjud yozuvlar qayta yaratilmaydi.
"""
from django.db import migrations

DISTRICTS = [
    'Bektemir', 'Chilonzor', 'Mirobod', "Mirzo Ulug'bek", 'Olmazor', 'Sergeli',
    'Shayxontohur', 'Uchtepa', 'Yakkasaroy', 'Yangihayot', 'Yashnobod', 'Yunusobod',
]

CATEGORIES = [
    ('Santexnik', '🚰'),
    ('Elektrik', '⚡'),
    ("Umumiy ta'mir", '🛠️'),
    ("Bo'yoqchi", '🎨'),
    ('Kafel ustasi', '🧱'),
    ('Tom va tunika', '🏠'),
    ('Payvandchi', '🔥'),
    ('Mebel ustasi', '🪚'),
]


def seed(apps, schema_editor):
    District = apps.get_model('catalog', 'District')
    Category = apps.get_model('catalog', 'Category')
    for name in DISTRICTS:
        District.objects.get_or_create(city='Toshkent', name=name)
    for name, icon in CATEGORIES:
        Category.objects.get_or_create(name=name, defaults={'icon': icon})


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
