
from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'order',
        'author',
        'target',
        'rating',
        'created_at',
    )

    list_filter = (
        'rating',
        'created_at',
    )

    search_fields = (
        'author__username',
        'target__user__username',
        'text',
    )

    readonly_fields = (
        'created_at',
    )

    list_per_page = 25
