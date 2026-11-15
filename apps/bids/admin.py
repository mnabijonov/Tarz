from django.contrib import admin

from .models import Bid


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):

    list_display = ('id', 'order', 'master', 'price', 'duration_days', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__id', 'master__user__first_name', 'master__user__phone', 'comments')
    list_select_related = ('order', 'master__user')
    raw_id_fields = ('order', 'master')
    readonly_fields = ('created_at',)
    list_per_page = 25
