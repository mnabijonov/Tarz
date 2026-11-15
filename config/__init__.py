# Django ishga tushganda Celery ilovasi ham yuklanadi (shared_task'lar shunga ulanadi).
from .celery import app as celery_app

__all__ = ('celery_app',)
