from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count
from django.utils.html import format_html

from apps.notifications.tasks import enqueue, notify_master_status
from apps.users.services import ask_reason_or_run

from .models import MasterProfile, PortfolioPhoto
from .services import approval_problems

S = MasterProfile.StatusChoice


def _image_preview(field, height=160):
    if not field:
        return "—"
    return format_html(
        '<a href="{0}" target="_blank"><img src="{0}" style="max-height:{1}px;border-radius:4px"></a>',
        field.url,
        height,
    )


def _notify_status(profile_id):
    transaction.on_commit(lambda: enqueue(notify_master_status, profile_id))


class PortfolioPhotoInline(admin.TabularInline):
    model = PortfolioPhoto
    extra = 0
    fields = ('preview', 'image', 'caption', 'created_at')
    readonly_fields = ('preview', 'created_at')

    @admin.display(description="Ko'rinish")
    def preview(self, obj):
        return _image_preview(obj.image, height=120)


class MasterProfileAdminForm(forms.ModelForm):

    class Meta:
        model = MasterProfile
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        # A1: rad etish faqat sabab bilan
        if cleaned.get('status') == S.REJECTED and not (cleaned.get('rejection_reason') or '').strip():
            self.add_error('rejection_reason', "Rad etish sababini kiriting.")
        return cleaned


@admin.register(MasterProfile)
class MasterProfileAdmin(admin.ModelAdmin):

    form = MasterProfileAdminForm
    inlines = [PortfolioPhotoInline]

    list_display = (
        'id',
        'user',
        'phone',
        'status',
        'portfolio_count',
        'has_document',
        'rating_avg',
        'jobs_done',
        'is_busy',
        'created_at',
    )

    list_filter = (
        'status',
        'is_busy',
        'categories',
        'districts',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__phone',
    )

    filter_horizontal = (
        'categories',
        'districts',
    )

    fieldsets = (
        (None, {
            'fields': ('user', 'status', 'rejection_reason', 'approval_check'),
        }),
        ("Profil", {
            'fields': ('categories', 'districts', 'experience_years', 'bio', 'is_busy'),
        }),
        ("Hujjat (faqat admin ko'radi)", {
            'fields': ('document_preview', 'document_photo'),
        }),
        ("Statistika", {
            'fields': ('rating_avg', 'jobs_done', 'created_at', 'updated_at'),
        }),
    )

    readonly_fields = (
        'approval_check',
        'document_preview',
        'rating_avg',
        'jobs_done',
        'created_at',
        'updated_at',
    )

    raw_id_fields = ('user',)

    actions = [
        'approve_masters',
        'reject_masters',
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('user')
            .annotate(_portfolio_count=Count('portfolio_photos', distinct=True))
        )

    @admin.display(description='Telefon')
    def phone(self, obj):
        return obj.user.phone

    @admin.display(description='Portfolio', ordering='_portfolio_count')
    def portfolio_count(self, obj):
        return obj._portfolio_count

    @admin.display(description='Hujjat', boolean=True)
    def has_document(self, obj):
        return bool(obj.document_photo)

    @admin.display(description='Hujjat rasmi')
    def document_preview(self, obj):
        return _image_preview(obj.document_photo, height=320)

    @admin.display(description="Tasdiqlashga tayyorligi")
    def approval_check(self, obj):
        if not obj.pk:
            return "—"
        problems = approval_problems(obj)
        if not problems:
            return format_html('<span style="color:green">{}</span>', "✔ Hammasi to'ldirilgan")
        return format_html(
            '<span style="color:#c00">{}</span>',
            '; '.join(problems),
        )

    def save_model(self, request, obj, form, change):
        obj._old_status = (
            MasterProfile.objects.filter(pk=obj.pk).values_list('status', flat=True).first()
            if change else None
        )
        if obj.status != S.REJECTED:
            obj.rejection_reason = ''
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # Kategoriya, tuman va portfolio saqlangandan keyin tekshiramiz
        super().save_related(request, form, formsets, change)
        obj = form.instance

        if obj.status == S.ACCEPTED:
            problems = approval_problems(obj)
            if problems:
                MasterProfile.objects.filter(pk=obj.pk).update(status=S.PENDING)
                obj.status = S.PENDING
                self.message_user(
                    request,
                    "Usta tasdiqlanmadi, holat 'kutilmoqda'da qoldi: " + '; '.join(problems),
                    messages.ERROR,
                )

        if obj.status != getattr(obj, '_old_status', None) and obj.status in (S.ACCEPTED, S.REJECTED):
            _notify_status(obj.pk)

    @admin.action(description="Tanlangan ustalarni tasdiqlash")
    def approve_masters(self, request, queryset):
        approved, skipped = 0, []
        for profile in queryset.select_related('user'):
            if profile.status == S.ACCEPTED:
                continue
            problems = approval_problems(profile)
            if problems:
                skipped.append(f"{profile}: {'; '.join(problems)}")
                continue
            profile.status = S.ACCEPTED
            profile.rejection_reason = ''
            profile.save(update_fields=['status', 'rejection_reason', 'updated_at'])
            _notify_status(profile.pk)
            approved += 1

        if approved:
            self.message_user(request, f"{approved} ta usta tasdiqlandi.", messages.SUCCESS)
        for line in skipped:
            self.message_user(request, f"Tasdiqlanmadi — {line}", messages.WARNING)

    @admin.action(description="Tanlangan ustalarni rad etish (sabab bilan)")
    def reject_masters(self, request, queryset):
        def apply(qs, reason):
            ids = list(qs.values_list('pk', flat=True))
            MasterProfile.objects.filter(pk__in=ids).update(status=S.REJECTED, rejection_reason=reason)
            for pk in ids:
                _notify_status(pk)
            return len(ids)

        return ask_reason_or_run(
            self, request, queryset,
            action='reject_masters',
            title="Ustalarni rad etish",
            submit_label="Rad etish",
            apply=apply,
        )


@admin.register(PortfolioPhoto)
class PortfolioPhotoAdmin(admin.ModelAdmin):

    list_display = ('id', 'master', 'preview', 'created_at')
    list_select_related = ('master__user',)

    search_fields = (
        'master__user__username',
        'master__user__phone',
    )

    @admin.display(description="Ko'rinish")
    def preview(self, obj):
        return _image_preview(obj.image, height=60)
