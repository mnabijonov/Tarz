
from django.db import transaction
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.masters.models import MasterProfile
from apps.users.models import User
from apps.users.permissions import (
    IsApprovedMaster,
    IsClient,
    NotBlocked,
)

from apps.notifications.tasks import enqueue, notify_order_cancelled, schedule_order_dispatch

from .models import Order, OrderPhoto
from .serializers import (
    OrderPhotoSerializers,
    OrderSerializers,
)


MAX_ORDER_PHOTOS = 5


def matches_master_categories(profile):
    """Buyurtma xizmat turi (Elektrik → Rozetka) ustaning kategoriyasiga mos keladimi.

    Usta odatda asosiy kategoriyani (Elektrik) tanlaydi, buyurtma esa xizmat turiga beriladi,
    shuning uchun ham o'zi, ham "otasi" bo'yicha tekshiramiz.
    """
    category_ids = profile.categories.values_list("pk", flat=True)
    return Q(category__in=category_ids) | Q(category__parent__in=category_ids)
MAX_BIDS_PER_ORDER = 7

ORDER_RELATED = ("client", "category", "district", "selected_bid__master__user")

ARCHIVE_STATUSES = (
    Order.StatusChoice.COMPLETED,
    Order.StatusChoice.CANCELLED,
)


class OrderListCreateView(generics.ListCreateAPIView):

    serializer_class = OrderSerializers

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
        IsClient,
    ]

    def get_queryset(self):
        qs = (
            Order.objects.filter(client=self.request.user)
            .select_related(*ORDER_RELATED)
            .prefetch_related("photos")
        )

        if self.request.query_params.get("archive") == "1":
            return qs.filter(status__in=ARCHIVE_STATUSES)

        return qs.exclude(status__in=ARCHIVE_STATUSES)

    def perform_create(self, serializer):
        order = serializer.save(client=self.request.user)
        # U3: mos ustalarga bot orqali yuborish (tranzaksiya tugagach, Celery orqali)
        transaction.on_commit(lambda: schedule_order_dispatch(order.pk))



class OrderDetailView(generics.RetrieveAPIView):

    serializer_class = OrderSerializers

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
    ]

    def get_queryset(self):
        user = self.request.user

        if user.role == User.RoleChoice.CLIENT:
            return Order.objects.filter(client=user)

        if user.role == User.RoleChoice.MASTER:
            profile = get_object_or_404(
                MasterProfile,
                user=user,
            )

            matching_new_orders = Order.objects.filter(
                matches_master_categories(profile),
                status=Order.StatusChoice.NEW,
                district__in=profile.districts.all(),
            )

            own_bid_orders = Order.objects.filter(
                bids__master__user=user,
            )

            return (
                (matching_new_orders | own_bid_orders)
                .distinct()
                .select_related(*ORDER_RELATED)
                .prefetch_related("photos")
            )

        return Order.objects.none()


class MasterFeedView(generics.ListAPIView):

    serializer_class = OrderSerializers

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
        IsApprovedMaster,
    ]

    def get_queryset(self):
        profile = get_object_or_404(
            MasterProfile,
            user=self.request.user,
        )

        # U4: faqat hali taklif qabul qiladigan buyurtmalar: o'zi taklif yubormagan,
        # 7 ta taklif to'lmagan, mijozi bloklanmagan.
        return (
            Order.objects.filter(
                matches_master_categories(profile),
                status=Order.StatusChoice.NEW,
                district__in=profile.districts.all(),
                client__is_blocked=False,
                client__is_active=True,
            )
            .exclude(client=self.request.user)
            .exclude(bids__master=profile)
            .annotate(bids_total=Count("bids", distinct=True))
            .filter(bids_total__lt=MAX_BIDS_PER_ORDER)
            .select_related(*ORDER_RELATED)
            .prefetch_related("photos")
            .order_by("-created_at")
        )


class MasterJobsView(generics.ListAPIView):
    """U6: "Mening ishlarim" - usta tanlangan buyurtmalar, mijoz kontakti bilan.

    ?status=selected|in_progress|completed bilan filtrlash mumkin.
    """

    serializer_class = OrderSerializers

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
        IsApprovedMaster,
    ]

    JOB_STATUSES = (
        Order.StatusChoice.SELECTED,
        Order.StatusChoice.IN_PROGRESS,
        Order.StatusChoice.COMPLETED,
    )

    def get_queryset(self):
        qs = (
            Order.objects.filter(
                selected_bid__master__user=self.request.user,
                status__in=self.JOB_STATUSES,
            )
            .select_related(*ORDER_RELATED)
            .prefetch_related("photos")
            .order_by("-updated_at")
        )

        status_filter = self.request.query_params.get("status")
        if status_filter in self.JOB_STATUSES:
            qs = qs.filter(status=status_filter)

        return qs


class OrderCancelView(APIView):

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
        IsClient,
    ]

    def post(self, request, pk):
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                pk=pk,
                client=request.user,
            )

            S = Order.StatusChoice

            if order.status not in (
                S.NEW,
                S.SELECTED,
                S.IN_PROGRESS,
            ):
                raise ValidationError(
                    "Bu buyurtmani bekor qilib bo'lmaydi."
                )

            reason = str(
                request.data.get("reason") or ""
            ).strip()

            if order.status != S.NEW and not reason:
                raise ValidationError({
                    "reason": (
                        "Usta tanlangandan keyin sabab "
                        "ko'rsatilishi shart."
                    )
                })

            had_selected_master = order.status != S.NEW

            order.status = S.CANCELLED
            order.cancel_reason = reason

            order.save(update_fields=[
                "status",
                "cancel_reason",
                "updated_at",
            ])

            if had_selected_master:
                transaction.on_commit(lambda: enqueue(notify_order_cancelled, order.pk))

        return Response(
            OrderSerializers(order, context={"request": request}).data
        )


class _MasterJobActionView(APIView):

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
        IsApprovedMaster,
    ]

    from_status = None

    def get_order(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_for_update(),
            pk=pk,
            selected_bid__master__user=request.user,
        )

        if order.status != self.from_status:
            raise ValidationError(
                f"Buyurtma holati '{order.status}'. "
                "Bu amalni bajarib bo'lmaydi."
            )

        return order


class OrderStartView(_MasterJobActionView):

    from_status = Order.StatusChoice.SELECTED

    def post(self, request, pk):
        with transaction.atomic():
            order = self.get_order(request, pk)

            order.status = Order.StatusChoice.IN_PROGRESS

            order.save(update_fields=[
                "status",
                "updated_at",
            ])

        return Response(
            OrderSerializers(order, context={"request": request}).data
        )


class OrderFinishView(_MasterJobActionView):

    from_status = Order.StatusChoice.IN_PROGRESS

    def post(self, request, pk):
        with transaction.atomic():
            order = self.get_order(request, pk)

            order.status = Order.StatusChoice.COMPLETED

            order.save(update_fields=[
                "status",
                "updated_at",
            ])

            MasterProfile.objects.filter(
                user=request.user,
            ).update(
                jobs_done=F("jobs_done") + 1
            )

        return Response(
            OrderSerializers(order, context={"request": request}).data
        )


class OrderPhotoCreateView(generics.CreateAPIView):

    serializer_class = OrderPhotoSerializers

    permission_classes = [
        IsAuthenticated,
        NotBlocked,
        IsClient,
    ]

    def perform_create(self, serializer):
        order_id = serializer.validated_data["order"].pk

        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                pk=order_id,
                client=self.request.user,
            )

            allowed_statuses = (
                Order.StatusChoice.NEW,
                Order.StatusChoice.SELECTED,
                Order.StatusChoice.IN_PROGRESS,
            )

            if order.status not in allowed_statuses:
                raise ValidationError(
                    "Bu buyurtmaga rasm yuklab bo'lmaydi."
                )

            if order.photos.count() >= MAX_ORDER_PHOTOS:
                raise ValidationError(
                    f"Ko'pi bilan {MAX_ORDER_PHOTOS} ta "
                    "rasm yuklash mumkin."
                )

            serializer.save(order=order)
