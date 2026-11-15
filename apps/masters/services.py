MIN_PORTFOLIO_PHOTOS = 3
MAX_PORTFOLIO_PHOTOS = 10


MESSAGES = {
    'uz': {
        'name': "Ism kiritilmagan",
        'category': "Kamida bitta kategoriya tanlanmagan",
        'district': "Kamida bitta ish tumani tanlanmagan",
        'portfolio': "Portfolioda kamida {min} ta rasm bo'lishi kerak (hozir {count} ta)",
        'document': "Hujjat rasmi yuklanmagan",
    },
    'ru': {
        'name': "Не указано имя",
        'category': "Не выбрана ни одна категория",
        'district': "Не выбран ни один район работы",
        'portfolio': "В портфолио нужно минимум {min} фото (сейчас {count})",
        'document': "Не загружен документ",
    },
}


def approval_problems(profile, language='uz'):
    """U1: tasdiqlashdan oldin to'ldirilishi shart bo'lgan narsalar ro'yxati (bo'sh = tayyor)."""
    text = MESSAGES.get(language, MESSAGES['uz'])
    problems = []
    user = profile.user
    if not (user.first_name or user.last_name):
        problems.append(text['name'])
    if not profile.categories.exists():
        problems.append(text['category'])
    if not profile.districts.exists():
        problems.append(text['district'])
    photo_count = profile.portfolio_photos.count()
    if photo_count < MIN_PORTFOLIO_PHOTOS:
        problems.append(text['portfolio'].format(min=MIN_PORTFOLIO_PHOTOS, count=photo_count))
    if not profile.document_photo:
        problems.append(text['document'])
    return problems
