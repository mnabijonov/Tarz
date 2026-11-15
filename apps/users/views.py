from django.contrib.auth.models import update_last_login
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, SelectRoleSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .services import validate_telegram_init_data
from .permissions import NotBlocked



# Create your views here.
class UserProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, NotBlocked]


    def get_object(self):
        return self.request.user
    




class TelegramAuthView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        init_data = request.data.get('initData')

        if not init_data:
            return Response(
                {'error': 'initData yuborilmadi'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            telegram_user = validate_telegram_init_data(init_data)

            telegram_id = telegram_user['id']

        except (ValueError, TypeError, KeyError, OverflowError):
            return Response(
                {'error': "Telegram ma'lumotlari noto'g'ri"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Foydalanuvchini faqat bot yaratadi (telefon ulashilgandan keyin).
        # Mini App to'g'ridan-to'g'ri ochilsa (menyu tugmasi, startapp havolasi)
        # ham raqamsiz kirish mumkin emas.
        user = User.objects.filter(telegram_id=telegram_id).first()

        if user is None or not user.phone:
            return Response(
                {
                    'error': "Avval botda telefon raqamingizni ulashing",
                    'code': 'phone_required',
                },
                status=status.HTTP_403_FORBIDDEN
            )

        if user.is_blocked or not user.is_active:
            return Response(
                {'error': 'Hisobingiz bloklangan', 'code': 'blocked'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Telegram'dagi ism va @username o'zgargan bo'lishi mumkin: har kirishda yangilanadi
        username = (telegram_user.get('username') or '')[:64]
        if username != user.telegram_username:
            user.telegram_username = username
            user.save(update_fields=['telegram_username'])

        created = user.last_login is None
        update_last_login(None, user)

        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Muvaffaqiyatli login',
            'is_new_user': created,
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })





class SelectRoleView(APIView):
    permission_classes = [IsAuthenticated, NotBlocked]

    def patch(self, request):
        serializer = SelectRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.role = serializer.validated_data['role']
        user.save(update_fields=['role'])

        return Response({
            'message': 'Rol muvaffaqiyatli tanlandi',
            'role': user.role,
        }, status=status.HTTP_200_OK)