
from rest_framework import serializers

from apps.users.services import contact_info, validate_image_file

from .models import Order, OrderPhoto


class OrderPhotoNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderPhoto
        fields = ["id", "image", "created_at"]
        read_only_fields = fields


CONTACT_VISIBLE_STATUSES = (
    Order.StatusChoice.SELECTED,
    Order.StatusChoice.IN_PROGRESS,
    Order.StatusChoice.COMPLETED,
)


class OrderSerializers(serializers.ModelSerializer):

    photos = OrderPhotoNestedSerializer(many=True, read_only=True)

    # M6: usta tanlangach ikkala tomonga bir-birining kontakti ochiladi.
    # Mijoz ustaning, tanlangan usta esa mijozning kontaktini ko'radi; boshqalar hech narsa ko'rmaydi.
    contact = serializers.SerializerMethodField()

    # Frontend uchun qulaylik maydonlari
    bids_count = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()
    my_bid = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "client",
            "category",
            "description",
            "district",
            "address",
            "desired_date",
            "budget_min",
            "budget_max",
            "status",
            "cancel_reason",
            "selected_bid",
            "photos",
            "contact",
            "bids_count",
            "is_reviewed",
            "my_bid",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "client",
            "status",
            "cancel_reason",
            "selected_bid",
            "created_at",
            "updated_at",
        ]

        extra_kwargs = {
            "category": {
                "required": True,
                "allow_null": False,
            },
            "district": {
                "required": True,
                "allow_null": False,
            },
        }

    def _user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def get_bids_count(self, obj):
        annotated = getattr(obj, "bids_total", None)
        return annotated if annotated is not None else obj.bids.count()

    def get_is_reviewed(self, obj):
        user = self._user()
        if user is None or user.pk != obj.client_id:
            return False
        from apps.reviews.models import Review
        return Review.objects.filter(order=obj, author=user).exists()

    def get_my_bid(self, obj):
        """Usta uchun: shu buyurtmaga yuborgan o'z taklifi (bo'lmasa null)."""
        user = self._user()
        if user is None or not user.is_authenticated or user.pk == obj.client_id:
            return None
        from apps.bids.models import Bid
        from apps.bids.serializers import BidSerializer
        bid = Bid.objects.filter(order=obj, master__user=user).first()
        return BidSerializer(bid).data if bid else None

    def get_contact(self, obj):
        request = self.context.get("request")
        if request is None or obj.status not in CONTACT_VISIBLE_STATUSES or obj.selected_bid is None:
            return None

        master_user = obj.selected_bid.master.user
        if request.user.pk == obj.client_id:
            data = contact_info(master_user)
            data["master_id"] = obj.selected_bid.master_id
            return data
        if request.user.pk == master_user.pk:
            data = contact_info(obj.client)
            data["address"] = obj.address
            return data
        return None

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Bu kategoriya hozir faol emas.")
        if not value.is_leaf:
            raise serializers.ValidationError("Aniq xizmat turini tanlang.")
        return value

    def validate_description(self, value):
        value = value.strip()

        if len(value) < 20:
            raise serializers.ValidationError(
                "Tavsif kamida 20 belgidan iborat bo'lsin."
            )

        return value

    def validate_budget_min(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Minimal budjet manfiy bo'lishi mumkin emas."
            )
        return value

    def validate_budget_max(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Maksimal budjet manfiy bo'lishi mumkin emas."
            )
        return value

    def validate(self, attrs):
        budget_min = attrs.get(
            "budget_min",
            getattr(self.instance, "budget_min", None),
        )
        budget_max = attrs.get(
            "budget_max",
            getattr(self.instance, "budget_max", None),
        )

        if (
            budget_min is not None
            and budget_max is not None
            and budget_min > budget_max
        ):
            raise serializers.ValidationError({
                "budget_max": (
                    "Maksimal budjet minimal budjetdan kichik "
                    "bo'lishi mumkin emas."
                )
            })

        return attrs


class OrderPhotoSerializers(serializers.ModelSerializer):

    class Meta:
        model = OrderPhoto
        fields = [
            "id",
            "order",
            "image",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_image(self, value):
        return validate_image_file(value)
