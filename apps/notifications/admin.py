from django.contrib import admin

from .models import OrderDispatch


@admin.register(OrderDispatch)
class OrderDispatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'master', 'wave', 'created_at')
    list_filter = ('wave', 'created_at')
    search_fields = ('order__id', 'master__user__phone', 'master__user__first_name')
    list_select_related = ('order', 'master__user')
    readonly_fields = ('order', 'master', 'wave', 'created_at')

    def has_add_permission(self, request):
        return False
