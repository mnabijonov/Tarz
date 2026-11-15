from django.urls import path
from apps.users import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("users/me/", views.UserProfileView.as_view(), name="user_profile"),
    path("users/telegram-auth/", views.TelegramAuthView.as_view(),name="telegram-auth"),
    path("users/token/refresh/",TokenRefreshView.as_view(), name="token-refresh"),
    path("users/select-role/", views.SelectRoleView.as_view(),name="select-role"),
]
