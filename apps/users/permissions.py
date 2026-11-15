
from rest_framework.permissions import BasePermission
from .models import User


class NotBlocked(BasePermission):
    message = "Hisobingiz bloklangan yoki faol emas."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and not user.is_blocked
        )


class IsClient(BasePermission):
    message = "Bu amal faqat mijozlar uchun."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.role == User.RoleChoice.CLIENT
        )


class IsMaster(BasePermission):
    message = "Bu amal faqat ustalar uchun."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.role == User.RoleChoice.MASTER
        )


class IsApprovedMaster(BasePermission):
    message = "Sizning usta profilingiz hali tasdiqlanmagan."

    def has_permission(self, request, view):
        user = request.user

        if not (
            user
            and user.is_authenticated
            and user.is_active
            and not user.is_blocked
            and user.role == User.RoleChoice.MASTER
        ):
            return False

        from apps.masters.models import MasterProfile

        return MasterProfile.objects.filter(
            user=user,
            status=MasterProfile.StatusChoice.ACCEPTED,
        ).exists()
