"""Har bir kategoriya ichidagi aniq xizmat turlari va rus tilidagi nomlar.

Mijoz buyurtma berganda avval kategoriyani (Elektrik), keyin aniq xizmatni
(Rozetka va o'chirgich) tanlaydi. Admin panelda istalgancha o'zgartirish mumkin.
Mavjud yozuvlar qayta yaratilmaydi, faqat bo'sh ruscha nom va tartib to'ldiriladi.
"""
from django.db import migrations

# (o'zbekcha nom, ruscha nom, ikonka, [(xizmat uz, xizmat ru), ...])
CATALOG = [
    ('Santexnik', 'Сантехник', '🚰', [
        ('Kran va smesitel', 'Краны и смесители'),
        ('Unitaz va rakovina', 'Унитаз и раковина'),
        ('Quvurlarni almashtirish', 'Замена труб'),
        ('Kanalizatsiyani tozalash', 'Прочистка канализации'),
        ('Suv isitgich (kolonka, boyler)', 'Водонагреватель (колонка, бойлер)'),
        ('Boshqa santexnika ishlari', 'Другие сантехнические работы'),
    ]),
    ('Elektrik', 'Электрик', '⚡', [
        ("Rozetka va o'chirgich", 'Розетки и выключатели'),
        ('Lyustra va yoritish', 'Люстры и освещение'),
        ('Elektr simlarini almashtirish', 'Замена электропроводки'),
        ('Elektr shchit va avtomatlar', 'Электрощит и автоматы'),
        ('Elektr nosozligini topish', 'Поиск неисправности'),
        ('Boshqa elektr ishlari', 'Другие электромонтажные работы'),
    ]),
    ("Umumiy ta'mir", 'Общий ремонт', '🛠️', [
        ("Kvartirani to'liq ta'mirlash", 'Ремонт квартиры под ключ'),
        ('Gipsokarton ishlari', 'Работы с гипсокартоном'),
        ('Shpaklyovka va suvoq', 'Шпаклёвка и штукатурка'),
        ('Pol yotqizish (laminat, parket)', 'Укладка пола (ламинат, паркет)'),
        ("Eshik va deraza o'rnatish", 'Установка дверей и окон'),
        ("Boshqa ta'mir ishlari", 'Другие ремонтные работы'),
    ]),
    ("Bo'yoqchi", 'Маляр', '🎨', [
        "Devor bo'yash|Покраска стен".split('|'),
        "Shift bo'yash|Покраска потолка".split('|'),
        "Fasad bo'yash|Покраска фасада".split('|'),
        "Gulqog'oz yopishtirish|Поклейка обоев".split('|'),
        "Boshqa bo'yoq ishlari|Другие малярные работы".split('|'),
    ]),
    ('Kafel ustasi', 'Плиточник', '🧱', [
        ('Hammom kafeli', 'Плитка в ванной'),
        ('Oshxona fartugi', 'Кухонный фартук'),
        ('Pol kafeli', 'Напольная плитка'),
        ('Boshqa kafel ishlari', 'Другие плиточные работы'),
    ]),
    ('Tom va tunika', 'Кровля и жесть', '🏠', [
        ('Tom yopish', 'Кровельные работы'),
        ("Tomni ta'mirlash (oqish)", 'Ремонт кровли (протечки)'),
        ('Tunika va profnastil', 'Жесть и профнастил'),
        ("Novlar o'rnatish", 'Установка водостоков'),
        ('Boshqa tom ishlari', 'Другие кровельные работы'),
    ]),
    ('Payvandchi', 'Сварщик', '🔥', [
        ('Darvoza va panjara', 'Ворота и решётки'),
        ('Metall konstruksiya', 'Металлоконструкции'),
        ("Payvandlab ta'mirlash", 'Сварочный ремонт'),
        ('Boshqa payvand ishlari', 'Другие сварочные работы'),
    ]),
    ('Mebel ustasi', 'Мебельщик', '🪚', [
        ("Mebel yig'ish", 'Сборка мебели'),
        ("Mebel ta'mirlash", 'Ремонт мебели'),
        ('Buyurtma asosida mebel', 'Мебель на заказ'),
        ("Oshxona mebelini o'rnatish", 'Установка кухни'),
        ('Boshqa mebel ishlari', 'Другие мебельные работы'),
    ]),
]

DISTRICTS_RU = {
    'Bektemir': 'Бектемирский', 'Chilonzor': 'Чиланзарский', 'Mirobod': 'Мирабадский',
    "Mirzo Ulug'bek": 'Мирзо-Улугбекский', 'Olmazor': 'Алмазарский', 'Sergeli': 'Сергелийский',
    'Shayxontohur': 'Шайхантахурский', 'Uchtepa': 'Учтепинский', 'Yakkasaroy': 'Яккасарайский',
    'Yangihayot': 'Янгихаётский', 'Yashnobod': 'Яшнабадский', 'Yunusobod': 'Юнусабадский',
}


def seed(apps, schema_editor):
    Category = apps.get_model('catalog', 'Category')
    District = apps.get_model('catalog', 'District')

    for district in District.objects.filter(name__in=DISTRICTS_RU, name_ru=''):
        district.name_ru = DISTRICTS_RU[district.name]
        district.save(update_fields=['name_ru'])

    for parent_position, (name, name_ru, icon, children) in enumerate(CATALOG, start=1):
        parent, _ = Category.objects.get_or_create(name=name, defaults={'icon': icon})
        if not parent.name_ru:
            parent.name_ru = name_ru
        if not parent.position:
            parent.position = parent_position
        parent.save(update_fields=['name_ru', 'position'])

        for position, (child_name, child_ru) in enumerate(children, start=1):
            child, created = Category.objects.get_or_create(
                name=child_name,
                defaults={'parent': parent, 'name_ru': child_ru, 'position': position},
            )
            if not created and child.parent_id is None and child.pk != parent.pk:
                # shu nomli kategoriya avval qo'lda yaratilgan bo'lsa, uni shu bo'limga biriktiramiz
                child.parent = parent
                child.save(update_fields=['parent'])


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_category_name_ru_position_district_name_ru'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
