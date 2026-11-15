from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count

from apps.bids.models import Bid
from apps.masters.models import MasterProfile

from .models import Order, OrderPhoto
from .services import select_bid


class BidCountFilter(admin.SimpleListFilter):
    """A2: taklifsiz qolgan buyurtmalarni tez topish."""

    title = 'Takliflar'
    parameter_name = 'bids'

    def lookups(self, request, model_admin):
        return (
            ('none', 'Taklifsiz'),
            ('some', 'Taklifi bor'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'none':
            return queryset.filter(_bids_count=0)
        if self.value() == 'some':
            return queryset.filter(_bids_count__gt=0)
        return queryset


class OrderAdminForm(forms.ModelForm):
    """A2: admin buyurtmaga ustani qo'lda biriktiradi (usta taklif yubormagan bo'lsa ham)."""

    assign_master = forms.ModelChoiceField(
        queryset=MasterProfile.objects.filter(
            status=MasterProfile.StatusChoice.ACCEPTED,
            user__is_blocked=False,
            user__is_active=True,
        ).select_related('user'),
        required=False,
        label='Ustani biriktirish',
        help_text="Faqat 'Yangi' holatdagi buyurtmaga. Saqlangach ikkala tomonga kontaktlar ochiladi.",
    )
    assign_price = forms.DecimalField(
        required=False, min_value=1, max_digits=12, decimal_places=2,
        label="Kelishilgan narx (so'm)",
        help_text="Usta allaqachon taklif yuborgan bo'lsa, bo'sh qoldirsangiz uning narxi olinadi.",
    )
    assign_duration_days = forms.IntegerField(
        required=False, min_value=1, label='Muddat (kun)',
    )

    class Meta:
        model = Order
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        master = cleaned.get('assign_master')
        if not master:
            return cleaned

        order = self.instance
        if not order.pk or order.status != Order.StatusChoice.NEW:
            raise forms.ValidationError("Ustani faqat 'Yangi' holatdagi buyurtmaga biriktirish mumkin.")
        if master.user_id == order.client_id:
            self.add_error('assign_master', "Mijozning o'zini usta qilib biriktirib bo'lmaydi.")

        has_bid = Bid.objects.filter(order=order, master=master).exists()
        if not has_bid:
            if cleaned.get('assign_price') is None:
                self.add_error('assign_price', "Usta taklif yubormagan: narxni kiriting.")
            if cleaned.get('assign_duration_days') is None:
                self.add_error('assign_duration_days', "Usta taklif yubormagan: muddatni kiriting.")
        return cleaned


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    form = OrderAdminForm

    list_display = (
        'id',
        'client',
        'category',
        'district',
        'status',
        'bids_count',
        'budget_min',
        'budget_max',
        'desired_date',
        'created_at',
    )

    list_filter = (
        'status',
        BidCountFilter,
        'category',
        'district',
        'created_at',
    )

    search_fields = (
        'client__username',
        'client__phone',
        'description',
        'address',
    )

    readonly_fields = (
        'selected_bid',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (None, {
            'fields': (
                'client', 'category', 'district', 'address', 'description',
                'desired_date', 'budget_min', 'budget_max',
            ),
        }),
        ('Holat', {
            'fields': ('status', 'cancel_reason', 'selected_bid', 'created_at', 'updated_at'),
        }),
        ("Ustani qo'lda biriktirish", {
            'fields': ('assign_master', 'assign_price', 'assign_duration_days'),
        }),
    )

    raw_id_fields = ('client',)
    list_per_page = 25

    actions = [
        'cancel_orders',
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('client', 'category', 'district')
            .annotate(_bids_count=Count('bids', distinct=True))
        )

    @admin.display(description='Takliflar', ordering='_bids_count')
    def bids_count(self, obj):
        return obj._bids_count

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        master = form.cleaned_data.get('assign_master')
        if not master:
            return

        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=obj.pk)
            if order.status != Order.StatusChoice.NEW:
                self.message_user(request, "Buyurtma holati o'zgargan, usta biriktirilmadi.", messages.ERROR)
                return

            bid = Bid.objects.filter(order=order, master=master).first()
            price = form.cleaned_data.get('assign_price')
            duration = form.cleaned_data.get('assign_duration_days')
            if bid is None:
                bid = Bid.objects.create(
                    order=order,
                    master=master,
                    price=price,
                    duration_days=duration,
                    comments="Admin tomonidan biriktirildi",
                )
            else:
                update_fields = []
                if price is not None:
                    bid.price = price
                    update_fields.append('price')
                if duration is not None:
                    bid.duration_days = duration
                    update_fields.append('duration_days')
                if update_fields:
                    bid.save(update_fields=update_fields)

            select_bid(order, bid)

        obj.status = order.status
        obj.selected_bid = order.selected_bid
        self.message_user(request, f"{master} buyurtma #{order.pk} ga biriktirildi.", messages.SUCCESS)

    @admin.action(description="Tanlangan buyurtmalarni bekor qilish")
    def cancel_orders(self, request, queryset):
        ids = list(queryset.values_list('pk', flat=True))
        Order.objects.filter(pk__in=ids).update(
            status=Order.StatusChoice.CANCELLED
        )


@admin.register(OrderPhoto)
class OrderPhotoAdmin(admin.ModelAdmin):

    list_display = ('id', 'order')
    search_fields = ('order__description',)
