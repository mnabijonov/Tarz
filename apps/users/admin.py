from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils import timezone

from .models import User
from .services import ask_reason_or_run


class TarzUserChangeForm(UserChangeForm):

    class Meta(UserChangeForm.Meta):
        model = User

    def clean(self):
        cleaned = super().clean()
        # A3: bloklashda sabab majburiy va saqlanadi
        if cleaned.get('is_blocked') and not (cleaned.get('block_reason') or '').strip():
            self.add_error('block_reason', "Bloklash sababini kiriting.")
        return cleaned


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    form = TarzUserChangeForm

    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'phone',
        'role',
        'is_blocked',
        'is_active',
        'is_staff',
    )

    list_filter = (
        'role',
        'is_blocked',
        'is_active',
        'is_staff',
    )

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'phone',
        'telegram_id',
        'telegram_username',
    )

    ordering = ('-date_joined',)

    readonly_fields = (
        'date_joined',
        'last_login',
        'blocked_at',
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Qo‘shimcha ma’lumotlar', {
            'fields': (
                'role',
                'phone',
                'telegram_id',
                'telegram_username',
                'language',
            )
        }),
        ('Bloklash', {
            'fields': (
                'is_blocked',
                'block_reason',
                'blocked_at',
            )
        }),
    )

    actions = [
        'block_users',
        'unblock_users',
    ]

    def save_model(self, request, obj, form, change):
        if 'is_blocked' in form.changed_data:
            if obj.is_blocked:
                obj.blocked_at = timezone.now()
            else:
                obj.blocked_at = None
                obj.block_reason = ''
        super().save_model(request, obj, form, change)

    @admin.action(description="Tanlangan foydalanuvchilarni bloklash (sabab bilan)")
    def block_users(self, request, queryset):
        def apply(qs, reason):
            return qs.update(is_blocked=True, block_reason=reason, blocked_at=timezone.now())

        return ask_reason_or_run(
            self, request, queryset,
            action='block_users',
            title="Foydalanuvchilarni bloklash",
            submit_label="Bloklash",
            apply=apply,
        )

    @admin.action(description="Blokdan chiqarish")
    def unblock_users(self, request, queryset):
        count = queryset.update(is_blocked=False, block_reason='', blocked_at=None)
        self.message_user(request, f"{count} ta foydalanuvchi blokdan chiqarildi.")
